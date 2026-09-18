"""
eval_conciseness_pairwise.py - Lección 6: Evaluador Pareado (Pairwise) de Concisión

Compara dos experimentos (por ejemplo, Agent v4 vs Agent v5) ante las mismas preguntas,
determinando cuál de las dos respuestas es más concisa pero preservando toda la información crucial.
Soporta tanto Ollama local (qwen2.5:7b) como OpenAI (gpt-5-nano), integrando medición de tokens con tiktoken.

Uso:
    uv run python module-2/lesson-6/eval_conciseness_pairwise.py <exp-a> <exp-b>
"""
import os
import re
import sys
from pathlib import Path
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


def conciseness_evaluator(inputs: dict, outputs: list[dict]) -> list[int]:
    """
    Evaluador pareado de concisión.
    outputs[0]: Respuesta del Agente A (ej. v4)
    outputs[1]: Respuesta del Agente B (ej. v5)
    Retorna: [score_a, score_b] donde 1 indica preferencia y 0 derrota/empate.
    """
    question = inputs.get("question", "")
    resp_a = outputs[0].get("answer", "") or outputs[0].get("output", "") or "N/A"
    resp_b = outputs[1].get("answer", "") or outputs[1].get("output", "") or "N/A"

    # Medición cuantitativa con token_utils
    metrics = token_utils.calculate_conciseness_metrics(resp_a, resp_b)

    # Evaluación cualitativa con el LLM Juez
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a conciseness evaluator. Respond with only a single number: 0, 1, or 2."
                },
                {
                    "role": "user",
                    "content": CONCISENESS_PROMPT.format(
                        question=question,
                        response_a=resp_a,
                        response_b=resp_b,
                    )
                }
            ],
            temperature=0.0,
        )

        content = response.choices[0].message.content.strip()
        match = re.search(r"[012]", content)
        preference = int(match.group(0)) if match else 0
    except Exception as e:
        print(f"Aviso en evaluación LLM pareada: {e}. Usando métrica de tokens cuantitativa.")
        preference = 2 if metrics["is_b_more_concise"] else 1

    if preference == 1:
        return [1, 0]  # A gana
    elif preference == 2:
        return [0, 1]  # B gana
    else:
        return [0, 0]  # Empate


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python eval_conciseness_pairwise.py <experiment-a> <experiment-b>")
        print("Ejemplo: python eval_conciseness_pairwise.py agent-v4-abc agent-v5-xyz")
        sys.exit(1)

    exp_a = sys.argv[1]
    exp_b = sys.argv[2]

    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 6: EVALUACIÓN PAREADA DE CONCISIÓN")
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
