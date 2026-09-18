"""
run_experiment.py - Lección 3: Ejecución de Experimentos en LangSmith

Orquesta un experimento conectando:
1. Target (Aplicación a evaluar): `dummy_app` o el agente real Emma (`agent_v5`).
2. Dataset: 'officeflow-dataset' en LangSmith.
3. Evaluators: `mentions_officeflow` (código) y métricas de tokens.

Uso:
    # Modo pedagógico rápido con dummy_app:
    uv run python module-2/lesson-3/run_experiment.py --mode dummy

    # Modo con el agente real Emma (usa Ollama local o OpenAI):
    uv run python module-2/lesson-3/run_experiment.py --mode agent
"""
import argparse
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

from langsmith import evaluate, aevaluate
from langsmith import uuid7
import token_utils


# ---------------------------------------------------------------------------
# 1. Targets (Aplicaciones Objetivo)
# ---------------------------------------------------------------------------

def dummy_app(inputs: dict) -> dict:
    """Aplicación simulada mínima del curso que responde mencionando 'OfficeFlow'."""
    return {"response": "Sure! In OfficeFlow, you can reset your password from the settings page."}


async def emma_agent_app(inputs: dict) -> dict:
    """Wrapper para evaluar al agente real Emma (agent_v5) con sesión aislada."""
    import agent_v5
    agent_v5.thread_id = str(uuid7())
    question = inputs.get("question", "")
    res = await agent_v5.chat(question)
    return {"response": res.get("output", ""), "messages": res.get("messages", [])}


# ---------------------------------------------------------------------------
# 2. Evaluadores Basados en Código (Deterministas)
# ---------------------------------------------------------------------------

def mentions_officeflow(run, example) -> dict:
    """Verifica si la respuesta generada menciona la marca 'officeflow'."""
    outputs = run.outputs if hasattr(run, "outputs") and run.outputs else run.get("outputs", {})
    text = str(outputs.get("response", "") or outputs.get("output", "")).lower()
    score = 1 if "officeflow" in text else 0
    return {
        "key": "mentions_officeflow",
        "score": score,
        "comment": "Menciona OfficeFlow" if score == 1 else "No menciona OfficeFlow",
    }


def token_efficiency_check(run, example) -> dict:
    """Mide el consumo de tokens y penaliza respuestas excesivamente largas (>150 tokens)."""
    outputs = run.outputs if hasattr(run, "outputs") and run.outputs else run.get("outputs", {})
    text = str(outputs.get("response", "") or outputs.get("output", ""))
    tokens = token_utils.count_tokens(text)
    # Puntuación 1 si es concisa (<= 120 tokens), 0 si es verborrágica
    is_concise = tokens <= 120
    return {
        "key": "is_concise",
        "score": 1 if is_concise else 0,
        "comment": f"Generó {tokens} tokens (Límite conciso: 120)",
    }


# ---------------------------------------------------------------------------
# 3. Función Principal de Lanzamiento
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Ejecutar experimento de evaluación en LangSmith")
    parser.add_argument(
        "--mode",
        choices=["dummy", "agent"],
        default="dummy",
        help="Elije 'dummy' para probar evaluate() al instante, o 'agent' para evaluar al agente Emma real.",
    )
    args = parser.parse_args()

    dataset_name = "officeflow-dataset"

    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 3: LANZAMIENTO DE EXPERIMENTO EN LANGSMITH")
    print("=" * 70)
    print(f"Modo seleccionado:  {args.mode.upper()}")
    print(f"Dataset objetivo:   {dataset_name}")
    print(f"Evaluadores:        [mentions_officeflow, token_efficiency_check]")
    print("=" * 70)

    if args.mode == "dummy":
        print("\nEjecutando experimento con Dummy App...")
        results = evaluate(
            dummy_app,
            data=dataset_name,
            evaluators=[mentions_officeflow, token_efficiency_check],
            experiment_prefix="dummy-app-experiment",
        )
        print("\n✅ Experimento completado con éxito.")
    else:
        print("\nCargando base de conocimiento de Emma...")
        import agent_v5
        kb_path = str(agent_dir / "knowledge_base")
        await agent_v5.load_knowledge_base(kb_dir=kb_path)

        print("\nEjecutando experimento con Agente Emma (Ollama / OpenAI)...")
        results = await aevaluate(
            emma_agent_app,
            data=dataset_name,
            evaluators=[mentions_officeflow, token_efficiency_check],
            experiment_prefix="emma-v5-experiment",
            max_concurrency=2,
        )
        print("\n✅ Experimento con el agente completado con éxito.")


if __name__ == "__main__":
    asyncio.run(main())
