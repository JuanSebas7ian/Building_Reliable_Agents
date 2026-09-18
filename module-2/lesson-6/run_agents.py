"""
run_agents.py - Lección 6: Ejecución de Experimentos Base para Comparación Pareada

Ejecuta secuencialmente al Agente v4 y al Agente v5 sobre 'officeflow-dataset',
generando dos experimentos independientes en LangSmith para ser comparados posteriormente.

Uso:
    uv run python module-2/lesson-6/run_agents.py
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

from langsmith import aevaluate, uuid7
import agent_v4
from agent_v4 import chat as chat_v4, load_knowledge_base as load_kb_v4
import agent_v5
from agent_v5 import chat as chat_v5, load_knowledge_base as load_kb_v5

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
    print("MÓDULO 2 - LECCIÓN 6: EJECUTANDO AGENTES V4 Y V5 PARA EVALUACIÓN PAREADA")
    print(f"Modelo:   {os.getenv('CHAT_MODEL', 'qwen2.5:7b')} ({os.getenv('OPENAI_BASE_URL', 'Ollama')})")
    print("=" * 70)

    # 1. Cargar bases de conocimiento
    print("Cargando bases de conocimiento...")
    await load_kb_v4(KB_DIR)
    await load_kb_v5(KB_DIR)

    # 2. Experimento con Agent v4
    print("\n[1/2] Lanzando experimento para Agent v4...")
    v4_results = await aevaluate(
        chat_wrapper_v4,
        data=DATASET_NAME,
        experiment_prefix="agent-v4",
        max_concurrency=2,
    )

    # 3. Experimento con Agent v5
    print("\n[2/2] Lanzando experimento para Agent v5...")
    v5_results = await aevaluate(
        chat_wrapper_v5,
        data=DATASET_NAME,
        experiment_prefix="agent-v5",
        max_concurrency=2,
    )

    print("\n" + "=" * 70)
    print("🎉 EXPERIMENTOS BASE COMPLETADOS:")
    print(f"  Exp A (v4): {v4_results.experiment_name}")
    print(f"  Exp B (v5): {v5_results.experiment_name}")
    print("\nSiguiente paso: Ejecutar la evaluación pareada:")
    print(f"  uv run python module-2/lesson-6/eval_conciseness_pairwise.py {v4_results.experiment_name} {v5_results.experiment_name}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
