"""
run_pairwise_experiment.py - Lección 6: Pipeline Todo-en-Uno de Evaluación Pareada

Automatiza el flujo completo de evaluación A/B en un único comando:
1. Corre Agent v4 contra 'officeflow-dataset'.
2. Corre Agent v5 contra 'officeflow-dataset'.
3. Ejecuta el juez pareado (eval_conciseness_pairwise) con barajado aleatorio (randomize_order=True)
   para determinar qué versión es más concisa y efectiva.

Uso:
    uv run python module-2/lesson-6/run_pairwise_experiment.py
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent
agent_dir = root_dir / "officeflow-agent"

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))
sys.path.insert(0, str(agent_dir))

load_dotenv(root_dir / ".env")

from langsmith import aevaluate, evaluate, uuid7
import agent_v4
from agent_v4 import chat as chat_v4, load_knowledge_base as load_kb_v4
import agent_v5
from agent_v5 import chat as chat_v5, load_knowledge_base as load_kb_v5
from eval_conciseness_pairwise import conciseness_evaluator

DATASET_NAME = "officeflow-dataset"
KB_DIR = str(agent_dir / "knowledge_base")


async def chat_wrapper_v4(inputs: dict) -> dict:
    agent_v4.thread_id = str(uuid7())
    question = inputs.get("question", "")
    result = await chat_v4(question)
    return {"answer": result["output"]}


async def chat_wrapper_v5(inputs: dict) -> dict:
    agent_v5.thread_id = str(uuid7())
    question = inputs.get("question", "")
    result = await chat_v5(question)
    return {"answer": result["output"]}


async def main():
    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 6: EXPERIMENTO COMPLETO PAREADO (A/B TESTING)")
    print(f"Modelo LLM: {os.getenv('CHAT_MODEL', 'qwen2.5:7b')} ({os.getenv('OPENAI_BASE_URL', 'Ollama')})")
    print("=" * 70)

    # Paso 1: Cargar bases de conocimiento
    print("Cargando bases de conocimiento...")
    await load_kb_v4(KB_DIR)
    await load_kb_v5(KB_DIR)

    # Paso 2: Experimento para agent v4
    print("\n[Paso 1/3] Ejecutando experimento para Agent v4...")
    v4_results = await aevaluate(
        chat_wrapper_v4,
        data=DATASET_NAME,
        experiment_prefix="agent-v4",
        max_concurrency=2,
    )

    # Paso 3: Experimento para agent v5
    print("\n[Paso 2/3] Ejecutando experimento para Agent v5...")
    v5_results = await aevaluate(
        chat_wrapper_v5,
        data=DATASET_NAME,
        experiment_prefix="agent-v5",
        max_concurrency=2,
    )

    v4_exp = v4_results.experiment_name
    v5_exp = v5_results.experiment_name

    print(f"\nExperimento A (v4): {v4_exp}")
    print(f"Experimento B (v5): {v5_exp}")

    # Paso 4: Evaluación pareada
    print("\n[Paso 3/3] Ejecutando evaluación pareada con conciseness_evaluator...")
    print("  Mitigación de sesgos activa: randomize_order=True")
    evaluate(
        (v4_exp, v5_exp),
        evaluators=[conciseness_evaluator],
        randomize_order=True,
    )

    print("\n" + "=" * 70)
    print("🎉 EVALUACIÓN PAREADA COMPLETADA CON ÉXITO.")
    print("Ingresa a LangSmith para comparar las curvas de preferencia entre v4 y v5.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
