"""
evaluating_agents.py - Lección 1: Fundamentos de Evaluación de Agentes

Demuestra cómo instrumentar una evaluación individual para el agente Emma de OfficeFlow,
incorporando:
- Soporte dual (Ollama local / OpenAI Cloud)
- Carga de base de conocimiento vectorial (nomic-embed-text)
- Telemetría de latencia exacta
- Conteo riguroso de tokens (con token_utils.py y tiktoken)
- Registro de trazabilidad completo en LangSmith

Uso:
    uv run python module-2/lesson-1/evaluating_agents.py
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Asegurar que las rutas a los módulos y al agente estén disponibles
current_dir = Path(__file__).resolve().parent
module_2_dir = current_dir.parent
root_dir = module_2_dir.parent
agent_dir = root_dir / "officeflow-agent"

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))
sys.path.insert(0, str(agent_dir))

# Cargar variables de entorno desde la raíz
load_dotenv(root_dir / ".env")

import agent_v5
from agent_v5 import chat, load_knowledge_base
import token_utils


async def run_single_evaluation(question: str):
    print("=" * 70)
    print("MÓDULO 2 - LECCIÓN 1: EVALUANDO AL AGENTE EMMA")
    print("=" * 70)
    print(f"🧠 Modelo LLM configurado:    {os.getenv('CHAT_MODEL', 'qwen2.5:7b')}")
    print(f"📡 Endpoint API:              {os.getenv('OPENAI_BASE_URL', 'http://localhost:11434/v1')}")
    print(f"📐 Modelo de Embeddings:      {os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')}")
    print(f"📊 Proyecto en LangSmith:     {os.getenv('LANGSMITH_PROJECT', 'lca-reliable-agents')}")
    print(f"🔍 Tracing activo:            {os.getenv('LANGSMITH_TRACING', 'false')}")
    print("=" * 70)

    # 1. Cargar Base de Conocimiento (RAG)
    kb_path = str(agent_dir / "knowledge_base")
    print("\n[1/3] Cargando base de conocimiento...")
    await load_knowledge_base(kb_dir=kb_path)

    # 2. Iniciar conversación de prueba
    print(f"\n[2/3] Enviando consulta de prueba:")
    print(f"  📥 Pregunta del usuario: \"{question}\"")

    start_time = time.perf_counter()
    resultado = await chat(question)
    elapsed_time = time.perf_counter() - start_time

    # 3. Métricas y Diagnóstico de Evaluación
    output_text = resultado.get("output", "")
    messages = resultado.get("messages", [])

    # Extraer llamadas a herramientas realizadas
    tool_calls_detected = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tool_calls_detected.append(tc["function"]["name"])

    # Conteo de tokens con tiktoken
    input_tokens = token_utils.count_tokens(question)
    output_tokens = token_utils.count_tokens(output_text)
    total_tokens = input_tokens + output_tokens

    # Velocidad de generación (Tokens por segundo)
    tps = output_tokens / elapsed_time if elapsed_time > 0 else 0.0

    print("\n[3/3] Resultados de la Evaluación:")
    print("-" * 70)
    print(f"  💬 Respuesta de Emma:\n{output_text}\n")
    print("-" * 70)
    print("📊 MÉTRICAS DE RENDIMIENTO:")
    print(f"  ⏱️  Latencia Total:         {elapsed_time:.2f} segundos")
    print(f"  📥 Tokens de Entrada:       {input_tokens} tokens")
    print(f"  📤 Tokens de Salida:        {output_tokens} tokens")
    print(f"  🔢 Tokens Totales:          {total_tokens} tokens")
    print(f"  ⚡ Rendimiento (Throughput): {tps:.1f} tokens/segundo")
    print(f"  🛠️  Herramientas usadas:    {tool_calls_detected or 'Ninguna (Respuesta directa)'}")
    print(f"  🧵 Thread ID de sesión:     {agent_v5.thread_id}")
    print("-" * 70)
    print("✅ La traza completa ha sido registrada en LangSmith para inspección jerárquica.")
    print("=" * 70)


if __name__ == "__main__":
    pregunta_ejemplo = "¿Tienen papel de copia en almacén y cuál es su política de devoluciones?"
    asyncio.run(run_single_evaluation(pregunta_ejemplo))
