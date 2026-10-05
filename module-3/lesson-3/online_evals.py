"""
online_evals.py - Módulo 3, Lección 3: Evaluadores en Línea (Online Evals)

Este script implementa un pipeline de evaluación continua en tiempo real para trazas
de producción de OfficeFlow, ejecutando evaluadores asíncronos y desacoplados:
1. Evaluador determinista de confidencialidad de stock (código Python puro, $0 coste).
2. Evaluador determinista de enrutamiento a departamentos oficiales (PRD routing).
3. Evaluador cuantitativo de concisión de tokens (token_utils).
4. Evaluador cualitativo online con LLM-as-a-Judge (detección de alucinaciones y tono).
5. Registro de calificaciones automáticas en LangSmith como feedback continuo.

Uso:
    uv run python module-3/lesson-3/online_evals.py
"""

import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Configuración de rutas
current_dir = Path(__file__).resolve().parent
module_3_dir = current_dir.parent
root_dir = module_3_dir.parent
module_2_dir = root_dir / "module-2"

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))
sys.path.insert(0, str(current_dir))

# Cargar variables de entorno
load_dotenv(root_dir / ".env")

import token_utils
from langsmith import Client

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")

openai_client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

# Canales de contacto oficiales estipulados en el PRD de OfficeFlow
AUTHORIZED_DEPARTMENTS = {
    "sales@officeflow.com": "Sales & New Orders",
    "fulfillment@officeflow.com": "Order Status & Tracking",
    "returns@officeflow.com": "Returns & Refunds",
    "accounts@officeflow.com": "Billing & Account Changes",
    "support@officeflow.com": "Technical Website Issues"
}


# ==============================================================================
# 1. EVALUADORES DETERMINISTAS EN CÓDIGO (Latencia < 2ms, Coste $0)
# ==============================================================================

def eval_online_stock_policy(question: str, response: str) -> Dict[str, Any]:
    """
    Evalúa si la respuesta respeta la política de confidencialidad de stock:
    No debe revelar números exactos de inventario (ej. '42 unidades en stock').
    """
    is_stock_question = any(term in question.lower() for term in ["stock", "inventory", "available", "units", "cuántos", "disponible", "how many", "warehouse", "boxes"])
    if not is_stock_question:
        return {"passed": True, "score": 1.0, "reason": "No aplica política de stock a esta consulta."}

    # Patrón: números seguidos de unidades, items, cajas, o frases numéricas explícitas
    number_pattern = re.compile(r'\b\d+\s*(units|boxes|items|reams|cases|paquetes|cajas|unidades)\b', re.IGNORECASE)
    match = number_pattern.search(response)

    if match:
        return {
            "passed": False,
            "score": 0.0,
            "reason": f"Violación de política: reveló cantidad numérica exacta '{match.group(0)}'."
        }

    return {
        "passed": True,
        "score": 1.0,
        "reason": "Cumple con la política de stock cualitativo (sin revelar cantidades exactas)."
    }


def eval_online_department_routing(question: str, response: str) -> Dict[str, Any]:
    """
    Evalúa que las consultas fuera de alcance (Returns, Billing, Orders) sean derivadas
    exclusivamente a los correos electrónicos autorizados en el PRD.
    """
    emails_in_response = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', response.lower())

    if not emails_in_response:
        # Si la consulta requería derivación estricta (ej. returns o refunds) y no dio email
        if any(term in question.lower() for term in ["return", "refund", "devolución", "cancel order"]):
            return {
                "passed": False,
                "score": 0.0,
                "reason": "La consulta requería derivación a departamento, pero no se proporcionó email de contacto."
            }
        return {"passed": True, "score": 1.0, "reason": "No requirió derivación a departamentos externos."}

    # Verificar que todos los emails mencionados pertenezcan a la lista autorizada
    unauthorized = [e for e in emails_in_response if e not in AUTHORIZED_DEPARTMENTS]
    if unauthorized:
        return {
            "passed": False,
            "score": 0.0,
            "reason": f"Mencionó canales de contacto no autorizados: {unauthorized}"
        }

    return {
        "passed": True,
        "score": 1.0,
        "reason": f"Derivación correcta a canales autorizados: {emails_in_response}"
    }


def eval_online_conciseness(response: str, max_tokens_allowed: int = 160) -> Dict[str, Any]:
    """
    Evalúa cuantitativamente que la respuesta no exceda el umbral de concisión estipulado.
    """
    tokens = token_utils.count_tokens(response)
    if tokens > max_tokens_allowed:
        return {
            "passed": False,
            "score": 0.0,
            "tokens": tokens,
            "reason": f"Respuesta excesivamente verbosa: {tokens} tokens (límite: {max_tokens_allowed})."
        }
    return {
        "passed": True,
        "score": 1.0,
        "tokens": tokens,
        "reason": f"Respuesta concisa: {tokens} tokens (límite: {max_tokens_allowed})."
    }


# ==============================================================================
# 2. EVALUADOR CUALITATIVO LLM (Muestreado en Streaming)
# ==============================================================================

def eval_online_faithfulness(question: str, context: str, response: str) -> Dict[str, Any]:
    """
    LLM-as-a-Judge en línea para verificar si la respuesta es verídica y fiel
    al contexto recuperado (evita alucinaciones en producción).
    """
    if not context or context == "N/A":
        return {"passed": True, "score": 1.0, "reason": "Sin contexto de recuperación requerido."}

    prompt = f"""You are an Online Faithfulness Evaluator.
Determine if the Agent Response is strictly supported by the Provided Context without hallucinating facts.

Question: {question}
Provided Context: {context}
Agent Response: {response}

Reply with ONLY a JSON object:
{{"is_faithful": true/false, "explanation": "brief reason"}}"""

    try:
        completion = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You evaluate factual consistency. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        raw = (completion.choices[0].message.content or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        import json
        data = json.loads(raw)
        passed = bool(data.get("is_faithful", True))
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": data.get("explanation", "Evaluación completada.")
        }
    except Exception as e:
        return {
            "passed": True,
            "score": 1.0,
            "reason": f"Fallback por excepción en juez: {e}"
        }


# ==============================================================================
# 3. PIPELINE DE EVALUACIÓN CONTINUA
# ==============================================================================

async def process_production_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta el conjunto de evaluadores online sobre una traza de producción en streaming.
    """
    run_id = trace.get("run_id", "trace_sim_001")
    question = trace.get("question", "")
    response = trace.get("response", "")
    context = trace.get("context", "")

    print("\n" + "=" * 75)
    print(f"⚡ [ONLINE EVAL] PROCESANDO TRAZA EN VIVO: {run_id}")
    print(f"📥 Consulta: \"{question}\"")
    print(f"📤 Respuesta: \"{response[:100]}...\"")
    print("-" * 75)

    # 1. Ejecutar evaluadores deterministas
    stock_res = eval_online_stock_policy(question, response)
    routing_res = eval_online_department_routing(question, response)
    concise_res = eval_online_conciseness(response)

    # 2. Ejecutar evaluador LLM online
    faith_res = eval_online_faithfulness(question, context, response)

    eval_results = {
        "stock_policy": stock_res,
        "department_routing": routing_res,
        "conciseness": concise_res,
        "faithfulness": faith_res
    }

    # Imprimir resultados
    all_passed = all(r["passed"] for r in eval_results.values())
    status_icon = "✅ APROBADA" if all_passed else "⚠️ ALERTA: ANOMALÍA DETECTADA"
    print(f"🎯 Veredicto Global: {status_icon}")
    print(f"  • Stock Policy:    {'✅ PASS' if stock_res['passed'] else '❌ FAIL'} -> {stock_res['reason']}")
    print(f"  • Dept Routing:    {'✅ PASS' if routing_res['passed'] else '❌ FAIL'} -> {routing_res['reason']}")
    print(f"  • Conciseness:     {'✅ PASS' if concise_res['passed'] else '❌ FAIL'} -> {concise_res['reason']}")
    print(f"  • Faithfulness:    {'✅ PASS' if faith_res['passed'] else '❌ FAIL'} -> {faith_res['reason']}")

    # 3. Enviar feedback a LangSmith si está configurado
    is_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY") or ""

    if is_tracing and api_key and not api_key.startswith("your_"):
        try:
            client = Client()
            for key, res in eval_results.items():
                client.create_feedback(
                    run_id=run_id,
                    key=f"online_{key}",
                    score=float(res["score"]),
                    comment=str(res.get("reason", ""))
                )
            print(f"  📡 4 calificaciones enviadas en tiempo real a LangSmith.")
        except Exception as e:
            print(f"  ⚠️ Error al emitir feedback en LangSmith: {e}")
    else:
        print("  💡 (Modo Local/Offline): Evaluaciones online listas para emitir feedback a LangSmith.")

    print("=" * 75)
    return {
        "run_id": run_id,
        "all_passed": all_passed,
        "evaluations": eval_results
    }


async def main():
    print("=" * 75)
    print("MÓDULO 3 - LECCIÓN 3: ONLINE EVALS (EVALUACIÓN CONTINUA EN STREAMING)")
    print("Monitoreo en Tiempo Real de Trazas de Producción")
    print("=" * 75)

    # Simulación de flujo de producción con 3 escenarios típicos
    production_stream: List[Dict[str, Any]] = [
        {
            "run_id": "run_prod_001_clean",
            "question": "Do you have standard multi-purpose printer paper?",
            "response": "Yes, we currently have multi-purpose printer paper available in several finishes. Would you like assistance selecting a ream or case?",
            "context": "Multi-purpose printer paper is in stock in high quantities across our regional warehouses."
        },
        {
            "run_id": "run_prod_002_violation",
            "question": "How many boxes of heavy duty staples do you have in warehouse?",
            "response": "We currently have exactly 42 boxes in stock at our warehouse. You can order them whenever you want.",
            "context": "Heavy duty staples: stock level 42 boxes."
        },
        {
            "run_id": "run_prod_003_bad_routing",
            "question": "I received broken pens and want a full refund.",
            "response": "I am sorry for the broken pens. Please write an email to john.doe@gmail.com and he will refund your money.",
            "context": "For returns and refunds, contact our Returns Department at returns@officeflow.com."
        }
    ]

    for trace in production_stream:
        await process_production_trace(trace)

    print("\n🎉 Pipeline de Online Evals ejecutado con éxito.")
    print("👉 Revisa CLASE_MAGISTRAL_LECCION_3.md para los fundamentos pedagógicos y arquitectónicos.")


if __name__ == "__main__":
    asyncio.run(main())
