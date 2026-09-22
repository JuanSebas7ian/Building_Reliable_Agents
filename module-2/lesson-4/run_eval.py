"""
run_eval.py - Lección 4: Evaluación Basada en Código (Determinista)

Ejecuta dos evaluadores deterministas contra 'officeflow-dataset':
1. `schema_before_query`: Verifica que Emma descubra el esquema SQL antes de consultar datos.
2. `check_no_exact_quantities`: Verifica que Emma no revele cantidades numéricas exactas de stock.
3. `token_efficiency`: Monitorea el consumo de tokens.

Uso:
    uv run python module-2/lesson-4/run_eval.py
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configuración de rutas
current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent
agent_dir = root_dir / "officeflow-agent"

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))
sys.path.insert(0, str(agent_dir))

load_dotenv(root_dir / ".env")

from langsmith import evaluate, uuid7
import agent_v5
from agent_v5 import chat, load_knowledge_base
from eval_schema_check import schema_before_query
from eval_stock_policy import check_no_exact_quantities
import token_utils


async def setup():
    """Carga la base de conocimiento vectorial antes de iniciar las evaluaciones."""
    kb_dir = str(agent_dir / "knowledge_base")
    print("Cargando base de conocimiento...")
    await load_knowledge_base(kb_dir)


def run_agent(inputs: dict) -> dict:
    """
    Función Target (Run Function) diseñada bajo las directrices del skill langsmith-evaluator.

    1. Aislamiento estricto: Genera un nuevo thread_id (UUIDv7) por cada fila del dataset
       para evitar contaminación de memoria conversacional entre preguntas.
    2. Extracción defensiva: Soporta diferentes claves de entrada ('question', 'input').
    3. Retorno enriquecido para trayectoria: Devuelve la respuesta final ('output'/'response')
       junto con la secuencia cronológica completa de 'messages' y 'tool_calls' para que los
       evaluadores de trayectoria (schema_before_query) puedan auditarlos sin pérdida de datos.
    """
    session_id = str(uuid7())
    agent_v5.thread_id = session_id

    question = inputs.get("question") or inputs.get("input") or str(inputs)
    result = asyncio.run(chat(question))
    output_text = result.get("output", "")
    messages_history = result.get("messages", [])

    return {
        "output": output_text,
        "response": output_text,
        "messages": messages_history,
        "tokens": token_utils.count_tokens(output_text),
        "thread_id": session_id,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 4: EVALUACIÓN DETERMINISTA BASADA EN CÓDIGO")
    print("=" * 70)
    print(f"Modelo:        {os.getenv('CHAT_MODEL', 'qwen2.5:7b')} ({os.getenv('OPENAI_BASE_URL', 'Ollama')})")
    print("Evaluadores:   [schema_before_query, check_no_exact_quantities]")
    print("=" * 70)

    asyncio.run(setup())

    results = evaluate(
        run_agent,
        data="officeflow-dataset",
        evaluators=[schema_before_query, check_no_exact_quantities],
        experiment_prefix="code-eval-v5",
    )

    print("\n✅ Evaluación de código finalizada. Revisa los resultados en LangSmith.")
