"""
eval_llm_judge.py - Lección 5: Evaluador con LLM-as-a-Judge (Soporte Dual Ollama / OpenAI)

Utiliza un LLM (ej. qwen2.5:7b local en Ollama o gpt-5-nano en OpenAI) como juez
para calificar aspectos cualitativos y subjetivos que el código puro no puede medir:
- Tono profesional, empático y cálido.
- Claridad y utilidad de la respuesta para el cliente.
- Apego a las directrices de atención al cliente de OfficeFlow.

Retorna un score (1 a 5 o binario) y una justificación (*reasoning*).
"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Rutas del proyecto
current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent

load_dotenv(root_dir / ".env")

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

JUDGE_PROMPT = """You are an expert QA evaluator for customer support interactions at OfficeFlow Supply Co.
Evaluate the assistant's response to the customer's question based on these criteria:
1. Helpfulness: Did it directly address the customer's request with accurate information?
2. Tone & Empathy: Was it warm, professional, and empathetic without robotic filler?
3. Policy Compliance: If unable to handle directly (returns, order tracking, technical issues), did it provide the correct department email or next steps?

Customer Question:
{question}

Assistant Response:
{response}

Respond in the following JSON format ONLY:
{{
    "score": <number between 1 and 5, where 5 is excellent and 1 is completely unhelpful or rude>,
    "passed": <true if score >= 3, false otherwise>,
    "reasoning": "<brief 1-2 sentence explanation of your score>"
}}"""


def helpfulness_and_tone_judge(run, example=None) -> dict:
    """
    Evaluador LLM-as-a-Judge compatible con LangSmith evaluate().
    Extrae question del input y response del output, e invoca al LLM juez.
    """
    _ = example  # Parámetro canónico de LangSmith para evaluadores offline
    # Extraer entradas y salidas
    inputs = run.inputs if hasattr(run, "inputs") and run.inputs else run.get("inputs", {})
    outputs = run.outputs if hasattr(run, "outputs") and run.outputs else run.get("outputs", {})

    question = str(inputs.get("question", "") or inputs.get("input", ""))
    response = str(outputs.get("answer", "") or outputs.get("output", "") or outputs.get("response", ""))

    if not question or not response:
        return {
            "key": "helpfulness_and_tone",
            "score": 0,
            "comment": "Pregunta o respuesta vacía.",
        }

    formatted_prompt = JUDGE_PROMPT.format(question=question, response=response)

    try:
        completion = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a customer support quality evaluator. Always respond with valid JSON."
                },
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.1,
        )

        content = completion.choices[0].message.content.strip()

        # Limpiar posibles bloques markdown ```json ... ``` devueltos por LLMs locales
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)
        raw_score = data.get("score", 3)
        normalized_score = round(raw_score / 5.0, 2)  # Normalizar de 0.0 a 1.0 para LangSmith
        reasoning = data.get("reasoning", "Evaluación completada")

        return {
            "key": "helpfulness_and_tone",
            "score": normalized_score,
            "comment": f"Calificación: {raw_score}/5. Motivo: {reasoning}",
        }

    except Exception as e:
        # Fallback de seguridad en caso de fallo de formato del LLM
        return {
            "key": "helpfulness_and_tone",
            "score": 0.5,
            "comment": f"Error al ejecutar el juez LLM: {str(e)}",
        }


if __name__ == "__main__":
    print("=" * 70)
    print("TEST DIAGNÓSTICO: EVALUADOR LLM-AS-A-JUDGE (helpfulness_and_tone_judge)")
    print("=" * 70)
    print(f"Juez usando modelo: {CHAT_MODEL} en {BASE_URL}")

    # Caso 1: Respuesta Excelente (Empática, informativa, correo correcto)
    good_run = {
        "inputs": {"question": "How do I return a damaged product?"},
        "outputs": {
            "output": (
                "I'm sorry to hear your item arrived damaged! While I can't process returns directly, "
                "our Returns Department will take care of you right away. Please email returns@officeflow.com "
                "with your order number. They typically respond within 4 business hours. Is there anything else I can help with?"
            )
        }
    }

    # Caso 2: Respuesta Deficiente (Cortante, sin empatía, sin datos de contacto)
    bad_run = {
        "inputs": {"question": "How do I return a damaged product?"},
        "outputs": {
            "output": "I don't handle returns. Not my department."
        }
    }

    print("\n1. Evaluando Respuesta Excelente (Buena atención):")
    res_good = helpfulness_and_tone_judge(good_run, {})
    print(f"   Score: {res_good['score']} | Comentario: {res_good['comment']}")

    print("\n2. Evaluando Respuesta Deficiente (Mala atención):")
    res_bad = helpfulness_and_tone_judge(bad_run, {})
    print(f"   Score: {res_bad['score']} | Comentario: {res_bad['comment']}")

    print("\n" + "=" * 70)
    print("✅ Prueba diagnóstica finalizada.")
    print("=" * 70)
