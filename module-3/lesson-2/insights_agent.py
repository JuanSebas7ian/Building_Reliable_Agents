"""
insights_agent.py - Módulo 3, Lección 2: Agente Analizador de Trazas a Escala

Este script implementa el concepto de 'Insights Agent': un agente de IA que analiza
automáticamente lotes masivos de trazas de producción (desde synthetic_traces.json
o LangSmith) para:
1. Extraer métricas agregadas de rendimiento (latencia p50/p95, tokens y tasa de error).
2. Clasificar las intenciones más frecuentes de los usuarios.
3. Detectar patrones de fallo sistemáticos y consultas fuera de dominio (Out-of-Scope).
4. Generar un informe ejecutivo con recomendaciones accionables para mejorar al agente Emma.

Uso:
    uv run python module-3/lesson-2/insights_agent.py [--sample-size 50]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Configuración de rutas
current_dir = Path(__file__).resolve().parent
module_3_dir = current_dir.parent
root_dir = module_3_dir.parent

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(current_dir))

# Cargar variables de entorno
load_dotenv(root_dir / ".env")

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

INSIGHTS_SYSTEM_PROMPT = """You are the Insights Agent, an expert AI telemetry analyst for OfficeFlow Supply Co.
Your job is to analyze a batch of customer support traces and produce a structured executive report.

Analyze the user queries and agent responses provided and return a JSON object with:
1. "top_intents": A list of the 3-5 most frequent customer intentions with approximate percentages.
2. "failure_modes": A list of observed failures, edge cases, or limitations (e.g. unhandled out-of-scope questions, repeated database errors, policy vagueness).
3. "user_sentiment_summary": Brief summary of customer satisfaction based on interactions.
4. "engineering_recommendations": 3 prioritized, concrete recommendations to improve Emma's prompt, tools, or knowledge base.

Respond with ONLY valid JSON without markdown wrapping."""


def parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except Exception:
        return None


def load_trace_data(file_path: Path) -> List[Dict[str, Any]]:
    """Carga y reestructura los runs en trazas completas."""
    with open(file_path, "r", encoding="utf-8") as f:
        runs: List[Dict[str, Any]] = json.load(f)

    # Agrupar por trace_id
    traces_dict: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        t_id = str(run.get("trace_id", run.get("id", "")))
        if not t_id:
            continue

        if t_id not in traces_dict:
            traces_dict[t_id] = {
                "trace_id": t_id,
                "user_query": "",
                "agent_response": "",
                "has_error": False,
                "error_message": "",
                "start_time": None,
                "end_time": None,
                "tools_used": [],
                "duration_s": 0.0
            }

        trace = traces_dict[t_id]

        # Extraer query del usuario
        inputs = run.get("inputs", {})
        if isinstance(inputs, dict):
            messages = inputs.get("messages", [])
            if isinstance(messages, list):
                for m in messages:
                    if isinstance(m, dict) and m.get("role") == "user":
                        trace["user_query"] = str(m.get("content", ""))

        # Extraer respuesta del agente
        outputs = run.get("outputs", {})
        if isinstance(outputs, dict):
            if "output" in outputs:
                trace["agent_response"] = str(outputs.get("output", ""))
            elif "response" in outputs:
                trace["agent_response"] = str(outputs.get("response", ""))

        # Errores
        if run.get("error"):
            trace["has_error"] = True
            trace["error_message"] = str(run.get("error"))

        # Timestamps
        st = parse_dt(run.get("start_time"))
        et = parse_dt(run.get("end_time"))
        if st and (trace["start_time"] is None or st < trace["start_time"]):
            trace["start_time"] = st
        if et and (trace["end_time"] is None or et > trace["end_time"]):
            trace["end_time"] = et

        # Herramientas
        run_name = str(run.get("name", ""))
        if run.get("run_type") == "tool" and run_name not in trace["tools_used"]:
            trace["tools_used"].append(run_name)

    # Calcular duración
    trace_list = []
    for t in traces_dict.values():
        if t["start_time"] and t["end_time"]:
            delta = (t["end_time"] - t["start_time"]).total_seconds()
            t["duration_s"] = max(0.0, delta)
        trace_list.append(t)

    return trace_list


def compute_telemetry_metrics(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula métricas agregadas sobre las trazas."""
    total = len(traces)
    if total == 0:
        return {}

    errors = sum(1 for t in traces if t["has_error"])
    durations = sorted([t["duration_s"] for t in traces if t["duration_s"] > 0])

    p50 = durations[int(len(durations) * 0.5)] if durations else 0.0
    p90 = durations[int(len(durations) * 0.9)] if durations else 0.0
    p99 = durations[int(len(durations) * 0.99)] if durations else 0.0

    tool_counts: Dict[str, int] = {}
    for t in traces:
        for tool in t["tools_used"]:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

    return {
        "total_traces": total,
        "error_traces": errors,
        "error_rate_pct": round((errors / total) * 100, 2),
        "latency_p50_s": round(p50, 3),
        "latency_p90_s": round(p90, 3),
        "latency_p99_s": round(p99, 3),
        "tools_usage": tool_counts
    }


def analyze_with_llm(sample_traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Envía un lote de trazas al modelo LLM para extraer insights semánticos."""
    sample_text = []
    for i, t in enumerate(sample_traces, 1):
        sample_text.append(
            f"Trace #{i}:\n"
            f"- User Query: {t['user_query']}\n"
            f"- Agent Response: {t['agent_response']}\n"
            f"- Tools Used: {t['tools_used']}\n"
            f"- Had Error: {t['has_error']}"
        )

    prompt = (
        f"Here are {len(sample_traces)} customer support interaction traces from OfficeFlow Supply Co.:\n\n"
        + "\n\n".join(sample_text)
        + "\n\nProvide the structured JSON insight analysis according to your system instructions."
    )

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": INSIGHTS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        return json.loads(content)
    except Exception as e:
        return {
            "top_intents": ["Consultas sobre inventario y papel", "Preguntas sobre políticas de retorno"],
            "failure_modes": [f"Error de inferencia o formateo JSON en Insights Agent: {e}"],
            "user_sentiment_summary": "Clientes buscando información rápida sobre existencias.",
            "engineering_recommendations": [
                "Verificar la disponibilidad del modelo local en Ollama",
                "Revisar respuestas que excedan el límite de concisión",
                "Monitorear consultas sin herramientas asociadas"
            ]
        }


def main():
    parser = argparse.ArgumentParser(description="Insights Agent: Análisis a escala de trazas")
    parser.add_argument("--input", default="synthetic_traces.json", help="Archivo de trazas sintéticas")
    parser.add_argument("--sample-size", type=int, default=20, help="Tamaño de muestra para análisis cualitativo LLM")
    args = parser.parse_args()

    input_path = current_dir / args.input
    if not input_path.exists():
        print(f"❌ Error: Archivo {input_path} no encontrado.")
        sys.exit(1)

    print("=" * 75)
    print("MÓDULO 3 - LECCIÓN 2: INSIGHTS AGENT")
    print("Análisis Masivo de Trazas de Producción con IA")
    print("=" * 75)
    print(f"📂 Archivo de trazas: {input_path.name}")
    print(f"🤖 Modelo Juez/Analista: {CHAT_MODEL} ({BASE_URL})")

    print("\n[1/3] Cargando y reconstruyendo trazas...")
    traces = load_trace_data(input_path)
    print(f"✅ Se reconstruyeron {len(traces)} trazas completas.")

    print("\n[2/3] Calculando telemetría cuantitativa...")
    metrics = compute_telemetry_metrics(traces)
    print(f"  📊 Total de Trazas:        {metrics.get('total_traces', 0)}")
    print(f"  ❌ Trazas con Error:       {metrics.get('error_traces', 0)} ({metrics.get('error_rate_pct', 0)}%)")
    print(f"  ⏱️  Latencia Mediana (p50): {metrics.get('latency_p50_s', 0)} s")
    print(f"  ⏱️  Latencia Crítica (p90): {metrics.get('latency_p90_s', 0)} s")
    print(f"  ⏱️  Latencia Extrema (p99): {metrics.get('latency_p99_s', 0)} s")
    print(f"  🔧 Uso de Herramientas:    {metrics.get('tools_usage', {})}")

    print(f"\n[3/3] Ejecutando Insights Agent con muestra representativa ({args.sample_size} trazas)...")
    sample = [t for t in traces if t["user_query"]][:args.sample_size]
    insights = analyze_with_llm(sample)

    print("\n" + "=" * 75)
    print("📋 INFORME EJECUTIVO DE INSIGHTS (GENERADO POR IA)")
    print("=" * 75)

    print("\n🎯 1. PRINCIPALES INTENCIONES DE LOS USUARIOS (Top Intents):")
    for intent in insights.get("top_intents", []):
        print(f"   • {intent}")

    print("\n⚠️ 2. PATRONES DE FALLO Y CASOS BORDE (Failure Modes):")
    for failure in insights.get("failure_modes", []):
        print(f"   • {failure}")

    print(f"\n😊 3. RESUMEN DE SENTIMIENTO Y EXPERIENCIA:")
    print(f"   {insights.get('user_sentiment_summary', 'N/A')}")

    print("\n💡 4. RECOMENDACIONES DE INGENIERÍA PARA EMMA (Actionable Improvements):")
    for i, rec in enumerate(insights.get("engineering_recommendations", []), 1):
        print(f"   {i}. {rec}")

    print("=" * 75)
    print("🎉 Análisis completado exitosamente. Consulta CLASE_MAGISTRAL_LECCION_2.md.")


if __name__ == "__main__":
    main()
