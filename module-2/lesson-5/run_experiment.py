"""
run_experiment.py - Lección 5: Evaluación con LLM-as-a-Judge

Ejecuta un experimento de evaluación cualitativa contra 'officeflow-dataset'
utilizando el evaluador LLM-as-a-Judge (funciona con Ollama local o OpenAI).

Uso:
    uv run python module-2/lesson-5/run_experiment.py
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configurar rutas
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
from agent_v4 import chat, load_knowledge_base
from eval_llm_judge import helpfulness_and_tone_judge

DATASET_NAME = "officeflow-dataset"


async def chat_wrapper(inputs: dict) -> dict:
    """
    Invoca al agente Emma (agent_v4) con thread_id independiente para cada ejemplo.
    
    Garantiza aislamiento de memoria, extracción defensiva de entradas
    y mapeo uniforme de claves de salida ('output', 'answer', 'response').
    """
    session_id = str(uuid7())
    agent_v4.thread_id = session_id
    question = inputs.get("question") or inputs.get("input") or str(inputs)
    result = await chat(question)
    output_text = result.get("output", "")
    return {
        "output": output_text,
        "answer": output_text,
        "response": output_text,
        "messages": result.get("messages", []),
        "thread_id": session_id,
    }


async def main():
    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 5: EVALUACIÓN CON LLM-AS-A-JUDGE")
    print("=" * 70)
    print(f"Modelo Evaluador / Agente: {os.getenv('CHAT_MODEL', 'qwen2.5:7b')}")
    print(f"Endpoint:                  {os.getenv('OPENAI_BASE_URL', 'http://localhost:11434/v1')}")
    print("Evaluador en ejecución:    helpfulness_and_tone_judge (Rúbrica 1-5)")
    print("=" * 70)

    # 1. Cargar Base de Conocimiento RAG
    kb_path = str(agent_dir / "knowledge_base")
    print("Cargando base de conocimiento...")
    await load_knowledge_base(kb_dir=kb_path)

    # 2. Ejecutar experimento con el juez LLM
    # Nota: max_concurrency=1 es ideal para Ollama local evitando sobrecarga de VRAM
    print("\nIniciando evaluación con aevaluate()...")
    results = await aevaluate(
        chat_wrapper,
        data=DATASET_NAME,
        evaluators=[helpfulness_and_tone_judge],
        experiment_prefix="llm-judge-v4",
        max_concurrency=1,
    )

    print("\n✅ Evaluación cualitativa completada con éxito.")
    return results


if __name__ == "__main__":
    asyncio.run(main())
