"""
Módulo 3 - Lección 3: Evaluador de Sentimientos y Empatía (Local & LangSmith)
=============================================================================
Este script implementa un evaluador de sentimientos y tono conversacional
para trazas de soporte al cliente, diseñado para correr:
1. De forma 100% local sin costos ni APIs externas (Heurístico / Léxico).
2. O con un modelo local mediante Ollama (Qwen2.5 / Llama 3) sin enviar datos a terceros.
3. Y opcionalmente emitir las métricas (Feedback) a LangSmith si se desea registrar.

¿Se necesita API Key de GPT (OpenAI) para correrlo en LangSmith?
-----------------------------------------------------------------------------
NO. En LangSmith:
- Si ejecutas el evaluador en tu propio entorno (Python SDK), solo envías los
  scores numéricos o categóricos calculados localmente mediante `client.create_feedback()`.
- LangSmith NO necesita saber qué modelo usaste, ni requiere OpenAI.
- Incluso dentro de LangSmith Cloud (Online Evaluators), se soportan proveedores
  como Anthropic, Google Gemini o endpoints custom compatibles con OpenAI.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
load_dotenv(root_dir / ".env")

# Importación segura de OpenAI (para Ollama o OpenAI)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None  # pyright: ignore[reportConstantRedefinition]
    OPENAI_AVAILABLE = False

# Importación segura de LangSmith
try:
    from langsmith import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    Client = None  # pyright: ignore[reportConstantRedefinition]
    LANGSMITH_AVAILABLE = False

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")


# ==============================================================================
# 1. EVALUADOR DE SENTIMIENTOS BASADO EN CÓDIGO (100% LOCAL, $0, SIN API KEY)
# ==============================================================================

# Diccionarios léxicos calibrados para atención al cliente
FRUSTRATION_KEYWORDS = {
    "broken", "damaged", "defective", "terrible", "worst", "unacceptable",
    "awful", "horrible", "furious", "angry", "upset", "disappointed",
    "useless", "scam", "waste", "ridiculous", "refund", "never again",
    "cancel", "hate", "unusable", "not working", "ruined", "failed"
}

SATISFACTION_KEYWORDS = {
    "thanks", "thank you", "great", "excellent", "awesome", "perfect",
    "appreciate", "helpful", "wonderful", "amazing", "good job", "love it",
    "pleased", "fantastic", "prompt", "resolved"
}

EMPATHY_PHRASES = [
    r"\b(i understand|i completely understand|we understand)\b",
    r"\b(i am (so )?sorry|we are (so )?sorry|apologize for the inconvenience)\b",
    r"\b(happy to help|glad to assist|pleasure helping)\b",
    r"\b(i appreciate your patience|thank you for your patience)\b",
    r"\b(let'?s get this sorted|i will take care of this)\b"
]

DISMISSIVE_PHRASES = [
    r"\b(not my problem|not our fault|read the policy)\b",
    r"\b(as i already said|i already told you)\b",
    r"\b(calm down|don'?t yell|stop complaining)\b",
    r"\b(nothing (we|i) can do)\b"
]


def eval_sentiment_heuristic(text: str) -> Dict[str, Any]:
    """
    Evalúa el sentimiento de un texto de usuario usando análisis léxico ponderado.
    Retorna:
    - polarity: float entre -1.0 (muy negativo/frustrado) y +1.0 (muy positivo).
    - label: 'POSITIVE', 'NEUTRAL', o 'NEGATIVE_FRUSTRATED'.
    - detected_terms: lista de palabras clave detectadas.
    """
    clean_text = text.lower()
    words = set(re.findall(r'\b[a-z]{3,}\b', clean_text))

    frustration_matches = [w for w in words if w in FRUSTRATION_KEYWORDS]
    satisfaction_matches = [w for w in words if w in SATISFACTION_KEYWORDS]

    # Presencia de signos de exclamación múltiples o MAYÚSCULAS intensas
    intense_caps = len(re.findall(r'\b[A-Z]{3,}\b', text))
    exclamations = text.count("!")

    # Cálculo de balance
    score = len(satisfaction_matches) * 0.4 - len(frustration_matches) * 0.5
    if exclamations > 1 and len(frustration_matches) > 0:
        score -= 0.3
    if intense_caps > 1 and len(frustration_matches) > 0:
        score -= 0.4

    polarity = max(-1.0, min(1.0, score))

    if polarity <= -0.2:
        label = "NEGATIVE_FRUSTRATED"
    elif polarity >= 0.2:
        label = "POSITIVE"
    else:
        label = "NEUTRAL"

    return {
        "polarity": round(polarity, 2),
        "label": label,
        "frustration_terms": frustration_matches,
        "satisfaction_terms": satisfaction_matches,
        "reason": f"Sentimiento {label} (Polaridad: {round(polarity, 2)}). Coincidencias negativas: {frustration_matches}, positivas: {satisfaction_matches}."
    }


def eval_agent_empathy_heuristic(customer_sentiment: str, agent_response: str) -> Dict[str, Any]:
    """
    Evalúa si la respuesta del agente muestra el nivel de empatía y profesionalismo
    adecuado al estado anímico del cliente.
    """
    resp_lower = agent_response.lower()

    empathy_hits = []
    for pattern in EMPATHY_PHRASES:
        if re.search(pattern, resp_lower):
            empathy_hits.append(pattern)

    dismissive_hits = []
    for pattern in DISMISSIVE_PHRASES:
        if re.search(pattern, resp_lower):
            dismissive_hits.append(pattern)

    # Si el agente usa frases displicentes, reprobado de inmediato
    if dismissive_hits:
        return {
            "passed": False,
            "score": 0.0,
            "tone": "DISMISSIVE_RUDE",
            "reason": f"Tono displicente detectado: violación de estándares de atención."
        }

    # Si el cliente estaba frustrado, el agente DEBE mostrar empatía
    if customer_sentiment == "NEGATIVE_FRUSTRATED":
        if empathy_hits:
            return {
                "passed": True,
                "score": 1.0,
                "tone": "EMPATHIC_PROFESSIONAL",
                "reason": f"Cliente frustrado atendido con empatía adecuada ({len(empathy_hits)} frases de disculpa/comprensión detectadas)."
            }
        else:
            return {
                "passed": False,
                "score": 0.4,
                "tone": "COLD_ROBOTIC",
                "reason": "El cliente expresó frustración o daño en su pedido, pero el agente respondió de forma fría sin disculpas ni empatía."
            }

    # Si el cliente era neutral o positivo, un tono profesional estándar es suficiente
    return {
        "passed": True,
        "score": 1.0,
        "tone": "PROFESSIONAL",
        "reason": "Tono profesional y adecuado a la consulta del cliente."
    }


# ==============================================================================
# 2. EVALUADOR DE SENTIMIENTOS CON LLM LOCAL (OLLAMA / QWEN / OPENAI)
# ==============================================================================

def eval_sentiment_llm(
    customer_query: str,
    agent_response: str,
    client: Optional[Any] = None,
    model: str = CHAT_MODEL
) -> Dict[str, Any]:
    """
    Evalúa el sentimiento y empatía usando un LLM local (Ollama) o endpoint remoto.
    No requiere API Key de GPT si se utiliza un modelo local como Qwen o Llama.
    """
    if not client:
        return {
            "available": False,
            "customer_sentiment": "UNKNOWN",
            "agent_empathy_score": 1.0,
            "reason": "Juez LLM omitido (sin cliente configurado)."
        }

    prompt = f"""You are an expert customer experience QA auditor.
Analyze the following customer interaction at OfficeFlow:

[CUSTOMER MESSAGE]:
"{customer_query}"

[AGENT RESPONSE]:
"{agent_response}"

Evaluate two dimensions:
1. Customer Sentiment: POSITIVE, NEUTRAL, or FRUSTRATED.
2. Agent Empathy: Score 0.0 to 1.0 (Did the agent acknowledge frustration, apologize for issues, or show warm professionalism?).

Respond ONLY with a valid JSON object:
{{
  "customer_sentiment": "POSITIVE" | "NEUTRAL" | "FRUSTRATED",
  "agent_empathy_score": 0.0 to 1.0,
  "agent_tone": "EMPATHIC" | "PROFESSIONAL" | "COLD" | "DISMISSIVE",
  "explanation": "<1 sentence explanation>"
}}
"""
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = res.choices[0].message.content or ""
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            return {
                "available": True,
                "customer_sentiment": parsed.get("customer_sentiment", "NEUTRAL"),
                "agent_empathy_score": float(parsed.get("agent_empathy_score", 1.0)),
                "agent_tone": parsed.get("agent_tone", "PROFESSIONAL"),
                "explanation": parsed.get("explanation", "Evaluación completada.")
            }
        return {"available": True, "customer_sentiment": "NEUTRAL", "agent_empathy_score": 1.0, "agent_tone": "PROFESSIONAL", "explanation": "Salida no estructurada del LLM."}
    except Exception as e:
        return {"available": False, "customer_sentiment": "UNKNOWN", "agent_empathy_score": 1.0, "reason": f"Fallo al invocar LLM: {e}"}


# ==============================================================================
# 3. PUBLICACIÓN DE FEEDBACK A LANGSMITH (OPCIONAL)
# ==============================================================================

def log_sentiment_feedback_to_langsmith(
    run_id: str,
    sentiment_result: Dict[str, Any],
    empathy_result: Dict[str, Any],
    ls_client: Optional[Any] = None
) -> None:
    """
    Envía los resultados de la evaluación local a LangSmith.
    NOTA TÉCNICA: Esto NO requiere API Key de GPT. LangSmith solo almacena
    los scores que tú calculaste en local ('sentiment', 'empathy').
    """
    if not ls_client or not hasattr(ls_client, "create_feedback"):
        print(f"    💡 [LOCAL MODE] Feedback calculado localmente (sin conexión a LangSmith).")
        return

    try:
        # 1. Registrar sentimiento del cliente
        sentiment_score = 1.0 if sentiment_result["label"] == "POSITIVE" else (0.5 if sentiment_result["label"] == "NEUTRAL" else 0.0)
        ls_client.create_feedback(
            run_id=run_id,
            key="customer_sentiment",
            score=sentiment_score,
            value=sentiment_result["label"],
            comment=sentiment_result["reason"]
        )

        # 2. Registrar empatía del agente
        ls_client.create_feedback(
            run_id=run_id,
            key="agent_empathy",
            score=empathy_result["score"],
            value=empathy_result["tone"],
            comment=empathy_result["reason"]
        )
        print(f"    ☁️ [LANGSMITH SYNC] Feedback registrado exitosamente para la traza {run_id}.")
    except Exception as e:
        print(f"    ⚠️ [LANGSMITH SYNC] No se pudo enviar feedback a LangSmith: {e}")


# ==============================================================================
# 4. CASOS DE PRUEBA Y DEMOSTRACIÓN COMPLETA
# ==============================================================================

def run_sentiment_eval_demo() -> None:
    print("=" * 75)
    print("MÓDULO 3 - LECCIÓN 3: EVALUADOR DE SENTIMIENTOS Y EMPATÍA EN LOCAL")
    print("Evaluación de Calidad Conversacional (Heurístico Local + Juez Ollama)")
    print("=" * 75)

    # Inicializar cliente OpenAI local (Ollama)
    llm_client = None
    if OPENAI_AVAILABLE and OpenAI is not None:
        try:
            llm_client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
            print(f"🤖 Juez LLM Local conectado en: {BASE_URL} (Modelo: {CHAT_MODEL})")
        except Exception:
            print("⚠️ Juez LLM Local no disponible. Utilizando evaluador léxico determinista.")

    # Inicializar cliente LangSmith (Opcional)
    ls_client = None
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    if LANGSMITH_AVAILABLE and Client is not None and langchain_api_key:
        try:
            ls_client = Client()
            print("☁️ Cliente LangSmith detectado: Las métricas calculadas se sincronizarán.")
        except Exception:
            print("💡 Modo Local: Evaluador ejecutándose sin LangSmith.")
    else:
        print("💡 Modo Local Puro: Sin dependencia de LangSmith ni de OpenAI GPT.")

    print("=" * 75)

    test_interactions = [
        {
            "id": "trace_sent_001_angry_customer_good_agent",
            "customer": "I received broken pens and shattered ink bottles! Everything inside my box is ruined, this is unacceptable and I want a full refund right now!!",
            "agent": "I am so sorry to hear that your items arrived broken and ruined. I completely understand how frustrating that is. Let's make this right immediately: please email returns@officeflow.com with your order number and we will issue a replacement or full refund right away."
        },
        {
            "id": "trace_sent_002_angry_customer_cold_agent",
            "customer": "Your package never arrived and the delivery failed! I have a major client meeting in 2 hours and now I have zero paper. Total disaster!!",
            "agent": "Tracking information indicates courier delay. Check account portal for fulfillment status."
        },
        {
            "id": "trace_sent_003_happy_customer",
            "customer": "Thank you so much! The highlighters arrived early and they work fantastic. Truly appreciate the prompt support.",
            "agent": "You are very welcome! It's our pleasure to help. Don't hesitate to reach out if you need anything else for your office."
        },
        {
            "id": "trace_sent_004_rude_agent",
            "customer": "Why was I charged twice for the dry erase boards? Please fix this billing mistake.",
            "agent": "It's not our fault if your bank processed a duplicate charge. Read our terms of service before complaining."
        }
    ]

    for item in test_interactions:
        run_id = item["id"]
        customer_msg = item["customer"]
        agent_msg = item["agent"]

        print(f"\n⚡ AUDITANDO INTERACCIÓN: [{run_id}]")
        print(f"👤 Cliente: \"{customer_msg}\"")
        print(f"🤖 Agente:  \"{agent_msg}\"")
        print("-" * 75)

        # 1. Evaluación Heurística (Zero Cost, Zero Dependencies, < 1ms)
        sentiment = eval_sentiment_heuristic(customer_msg)
        empathy = eval_agent_empathy_heuristic(sentiment["label"], agent_msg)

        status_emoji = "✅" if empathy["passed"] else "❌"
        print(f"  • Sentimiento del Cliente: {sentiment['label']} (Polaridad: {sentiment['polarity']})")
        print(f"  • Evaluación de Empatía:   {status_emoji} Tono: {empathy['tone']} (Score: {empathy['score']})")
        print(f"    Razón: {empathy['reason']}")

        # 2. Evaluación con LLM Local (si está disponible)
        if llm_client:
            llm_eval = eval_sentiment_llm(customer_msg, agent_msg, client=llm_client, model=CHAT_MODEL)
            if llm_eval.get("available"):
                print(f"  • [Juez LLM Local]: Sentimiento={llm_eval.get('customer_sentiment')} | Score Empatía={llm_eval.get('agent_empathy_score')} | Tono={llm_eval.get('agent_tone')}")
                print(f"    Explicación LLM: \"{llm_eval.get('explanation')}\"")

        # 3. Opcional: Publicar feedback a LangSmith
        log_sentiment_feedback_to_langsmith(run_id, sentiment, empathy, ls_client)

    print("\n" + "=" * 75)
    print("🎯 CONCLUSIÓN DEL ANÁLISIS DE SENTIMIENTOS:")
    print("1. El evaluador opera 100% en local sin API key de GPT ni dependencias cloud.")
    print("2. Si deseas ver las métricas en LangSmith, ejecutas este evaluador localmente y envías")
    print("   el score mediante `client.create_feedback()`. ¡LangSmith solo almacena números/etiquetas!")
    print("=" * 75)


if __name__ == "__main__":
    run_sentiment_eval_demo()
