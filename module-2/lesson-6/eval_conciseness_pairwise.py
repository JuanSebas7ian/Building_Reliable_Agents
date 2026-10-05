"""
eval_conciseness_pairwise.py - Lección 6: Evaluador Pareado (Pairwise) de Concisión

Compara dos respuestas o dos experimentos de agentes (ej. Agent v4 vs Agent v5) ante las mismas preguntas,
determinando cuál de las dos respuestas es más concisa pero preservando toda la información crucial.
Soporta tanto Ollama local (qwen2.5:7b) como OpenAI (gpt-4o-mini / gpt-5-nano), integrando medición de tokens con tiktoken.

Uso:
    1. Diagnóstico local / prueba unitaria:
       uv run python module-2/lesson-6/eval_conciseness_pairwise.py

    2. Evaluación pareada de experimentos en LangSmith:
       uv run python module-2/lesson-6/eval_conciseness_pairwise.py <exp-a> <exp-b>
"""
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import evaluate

# Rutas del proyecto
current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))

load_dotenv(root_dir / ".env")

import token_utils

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

CONCISENESS_PROMPT = """You are evaluating two responses to the same customer question.
Determine which response is MORE CONCISE while still providing all crucial information.

**Conciseness** means getting straight to the point, avoiding filler, and not repeating information.
**Crucial information** includes direct answers, necessary context, and required next steps.

A shorter response is NOT automatically better if it omits crucial information.

**Question:** {question}

**Response A:**
{response_a}

**Response B:**
{response_b}

Output your verdict as a single number ONLY:
1 if Response A is more concise while preserving crucial information
2 if Response B is more concise while preserving crucial information
0 if they are roughly equal"""


def conciseness_evaluator(
    runs: Optional[Sequence[Any]] = None,
    example: Optional[Any] = None,
    *,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Evaluador pareado de concisión para LangSmith y ejecuciones directas.
    Compatible con la firma de COMPARATIVE_EVALUATOR_T de LangSmith: (runs, example) -> dict.
    """
    # Si se pasa un diccionario como primer argumento posicional (modo test directo)
    if isinstance(runs, dict) and inputs is None:
        inputs = runs
        runs = None
    if isinstance(example, list) and outputs is None:
        outputs = example
        example = None

    # 1. Extracción de inputs de forma defensiva
    question = ""
    ex_inputs: Any = getattr(example, "inputs", None)
    if inputs and isinstance(inputs, dict):
        question = str(inputs.get("question", "") or inputs.get("input", ""))
    elif ex_inputs and isinstance(ex_inputs, dict):
        question = str(ex_inputs.get("question", "") or ex_inputs.get("input", ""))
    elif runs and len(runs) > 0:
        r0_in: Any = getattr(runs[0], "inputs", {}) or {}
        if isinstance(r0_in, dict):
            question = str(r0_in.get("question", "") or r0_in.get("input", ""))

    # 2. Extracción de outputs de forma defensiva
    resp_a = "N/A"
    resp_b = "N/A"
    if outputs and len(outputs) >= 2:
        out_0 = outputs[0] if isinstance(outputs[0], dict) else {}
        out_1 = outputs[1] if isinstance(outputs[1], dict) else {}
        resp_a = str(out_0.get("answer", "") or out_0.get("output", "") or out_0.get("response", "") or "N/A")
        resp_b = str(out_1.get("answer", "") or out_1.get("output", "") or out_1.get("response", "") or "N/A")
    elif runs and len(runs) >= 2:
        out_0: Any = getattr(runs[0], "outputs", {}) or {}
        out_1: Any = getattr(runs[1], "outputs", {}) or {}
        if isinstance(out_0, dict):
            resp_a = str(out_0.get("answer", "") or out_0.get("output", "") or out_0.get("response", "") or "N/A")
        if isinstance(out_1, dict):
            resp_b = str(out_1.get("answer", "") or out_1.get("output", "") or out_1.get("response", "") or "N/A")

    # 3. Medición cuantitativa de tokens con token_utils
    metrics = token_utils.calculate_conciseness_metrics(resp_a, resp_b)

    # 4. Evaluación cualitativa con el LLM Juez
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a conciseness evaluator. Respond with only a single number: 0, 1, or 2.",
                },
                {
                    "role": "user",
                    "content": CONCISENESS_PROMPT.format(
                        question=question,
                        response_a=resp_a,
                        response_b=resp_b,
                    ),
                },
            ],
            temperature=0.0,
        )

        content = (response.choices[0].message.content or "").strip()
        match = re.search(r"[012]", content)
        preference = int(match.group(0)) if match else 0
    except Exception as e:
        print(f"Aviso en evaluación LLM pareada: {e}. Usando métrica cuantitativa de tokens.")
        preference = 2 if metrics["is_b_more_concise"] else 1

    # 5. Mapeo a identificadores de run o etiquetas A/B
    id_a = "A"
    id_b = "B"
    if runs and len(runs) >= 2:
        id_a = getattr(runs[0], "id", id_a)
        id_b = getattr(runs[1], "id", id_b)

    if preference == 1:
        scores = {id_a: 1, id_b: 0}
        verdict = "Respuesta A es más concisa y efectiva"
    elif preference == 2:
        scores = {id_a: 0, id_b: 1}
        verdict = "Respuesta B es más concisa y efectiva"
    else:
        scores = {id_a: 0, id_b: 0}
        verdict = "Ambas respuestas son equivalentes"

    comment = (
        f"{verdict}. Tokens A: {metrics['tokens_a']} | Tokens B: {metrics['tokens_b']}. "
        f"Ahorro de tokens en B vs A: {metrics['tokens_saved']} ({metrics['percent_reduction']}%)."
    )

    return {
        "key": "conciseness_preference",
        "scores": scores,
        "comment": comment,
    }


if __name__ == "__main__":
    if len(sys.argv) == 3:
        exp_a = sys.argv[1]
        exp_b = sys.argv[2]

        print("=" * 70)
        print("MÓDULO 2 - LECCIÓN 6: EVALUACIÓN PAREADA DE CONCISIÓN (LANGSMITH)")
        print(f"Juez LLM:           {CHAT_MODEL} ({BASE_URL})")
        print(f"Experimento A:      {exp_a}")
        print(f"Experimento B:      {exp_b}")
        print(f"Randomize Order:    True (Mitigación de Position Bias)")
        print("=" * 70)

        evaluate(
            (exp_a, exp_b),
            evaluators=[conciseness_evaluator],
            randomize_order=True,
        )
    else:
        print("=" * 70)
        print("TEST DIAGNÓSTICO: JUEZ PAREADO DE CONCISIÓN (eval_conciseness_pairwise)")
        print("=" * 70)
        print(f"Juez LLM: {CHAT_MODEL} en {BASE_URL}")

        # Caso 1: Comparación clásica Emma v4 (verbosa) vs Emma v5 (optimizada concisa)
        q1 = "Do you carry standard letter size copy paper?"
        resp_v4 = (
            "Yes, we do! We carry several types of copy paper. Are you looking for "
            "standard 8.5x11 inch letter size, or do you need a specific weight or finish? "
            "I can check what we have in stock."
        )
        resp_v5 = "Yes! We carry several types. Are you looking for standard 8.5x11, or a specific weight or finish?"

        print("\n--- CASO 1: Emma v4 (Verbosa) vs Emma v5 (Concisa) ---")
        print(f"Pregunta:   {q1}")
        print(f"Resp A(v4): {resp_v4}")
        print(f"Resp B(v5): {resp_v5}")

        res1 = conciseness_evaluator(
            inputs={"question": q1},
            outputs=[{"output": resp_v4}, {"output": resp_v5}],
        )
        print(f"Scores:     {res1['scores']}")
        print(f"Comentario: {res1['comment']}")

        # Caso 2: Concisión excesiva que omite información crucial (Penalización esperada)
        q2 = "How do I return a damaged product?"
        resp_full = (
            "While I cannot process returns directly, our Returns Department will help you at "
            "returns@officeflow.com or 1-800-OFFICE-1 ext. 3. They typically respond within 4 business hours."
        )
        resp_too_brief = "Email customer service."

        print("\n--- CASO 2: Respuesta Completa vs Respuesta Demasiado Breve (Omite Datos Cruciales) ---")
        print(f"Pregunta:   {q2}")
        print(f"Resp A:     {resp_full}")
        print(f"Resp B:     {resp_too_brief}")

        res2 = conciseness_evaluator(
            inputs={"question": q2},
            outputs=[{"output": resp_full}, {"output": resp_too_brief}],
        )
        print(f"Scores:     {res2['scores']}")
        print(f"Comentario: {res2['comment']}")

        print("\n" + "=" * 70)
        print("✅ Test diagnóstico completado con éxito.")
        print("Para comparar dos experimentos reales en LangSmith ejecuta:")
        print("  uv run python module-2/lesson-6/eval_conciseness_pairwise.py <exp-a> <exp-b>")
        print("=" * 70)
