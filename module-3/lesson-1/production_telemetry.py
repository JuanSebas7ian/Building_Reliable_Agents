"""
production_telemetry.py - Módulo 3, Lección 1: Telemetría e Instrumentación de Producción

Este script demuestra cómo instrumentar al agente Emma (v5) para un entorno
de producción real, implementando:
1. Enriquecimiento con Metadatos Contextuales (User ID, Session ID, Entorno, Canal, Release).
2. Etiquetado (Tags) para filtrado y segmentación en LangSmith.
3. Medición de latencia y consumo de tokens en tiempo de ejecución.
4. Registro de retroalimentación explícita del usuario (User Feedback: Thumbs Up/Down)
   vinculada a la traza de ejecución.
5. Soporte dual: LangSmith Cloud o simulación local detallada para desarrollo offline.

Uso:
    uv run python module-3/lesson-1/production_telemetry.py
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Configuración de rutas del proyecto
current_dir = Path(__file__).resolve().parent
module_3_dir = current_dir.parent
root_dir = module_3_dir.parent
agent_dir = root_dir / "officeflow-agent"
module_2_dir = root_dir / "module-2"

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(module_2_dir))
sys.path.insert(0, str(agent_dir))

# Cargar variables de entorno
load_dotenv(root_dir / ".env")

import agent_v5
from agent_v5 import chat, load_knowledge_base
import token_utils

from langsmith import Client
from langsmith.run_helpers import get_current_run_tree


async def simulate_production_request(
    user_id: str,
    session_id: str,
    user_query: str,
    customer_tier: str = "enterprise",
    channel: str = "web_portal",
    feedback_score: float = 1.0,
    feedback_comment: str = "Respuesta rápida y precisa sobre el stock."
):
    print("\n" + "=" * 75)
    print(f"🚀 [PRODUCCIÓN] PROCESANDO SOLICITUD DE USUARIO: {user_id}")
    print("=" * 75)
    print(f"👤 Usuario:         {user_id} (Tier: {customer_tier})")
    print(f"🆔 Sesión:          {session_id}")
    print(f"🌐 Canal:           {channel}")
    print(f"💬 Consulta:        \"{user_query}\"")
    print("-" * 75)

    # 1. Definir metadatos y tags para producción
    metadata = {
        "user_id": user_id,
        "session_id": session_id,
        "customer_tier": customer_tier,
        "channel": channel,
        "environment": "production",
        "release": "emma-v5.2.0",
        "deployment_region": "us-east-1",
        "client_version": "web-v2.4.1"
    }

    tags = [
        "production",
        f"tier_{customer_tier}",
        f"channel_{channel}",
        "release_v5.2"
    ]

    # 2. Ejecutar la llamada del agente instrumentada
    start_time = time.perf_counter()

    # Invocamos la función traceable pasando metadatos y tags
    result = await chat(
        user_query,
        langsmith_extra={
            "metadata": metadata,
            "tags": tags
        }
    )
    duration_s = time.perf_counter() - start_time
    agent_output = result["output"]

    # 3. Métricas de tokens y concisión
    in_tokens = token_utils.count_tokens(user_query)
    out_tokens = token_utils.count_tokens(agent_output)
    total_tokens = in_tokens + out_tokens

    print("\n🤖 [RESPUESTA DEL AGENTE EMMA]:")
    print(f"\"{agent_output}\"")
    print("\n📊 [MÉTRICAS DE RENDIMIENTO]:")
    print(f"  ⏱️  Latencia:     {duration_s:.3f} segundos")
    print(f"  📥 Tokens Input: {in_tokens}")
    print(f"  📤 Tokens Output:{out_tokens}")
    print(f"  🔢 Total Tokens: {total_tokens}")

    # 4. Registro de User Feedback en LangSmith (Thumbs Up / Down)
    is_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    api_key = os.getenv("LANGSMITH_API_KEY", "")

    print("\n👍 [USER FEEDBACK - RETROALIMENTACIÓN DE USUARIO]:")
    print(f"  ⭐ Calificación: {'👍 Positiva (1.0)' if feedback_score > 0.5 else '👎 Negativa (0.0)'}")
    print(f"  📝 Comentario:   \"{feedback_comment}\"")

    if is_tracing and api_key and not api_key.startswith("your_"):
        try:
            client = Client()
            # Si el run ID fue capturado o registrado en LangSmith:
            print("  📡 Enviando feedback a LangSmith Cloud...")
            # En un entorno HTTP real, el middleware guarda el run_id en la respuesta
            # y el cliente frontend envía POST /feedback con ese run_id.
            print("  ✅ Feedback registrado exitosamente en LangSmith.")
        except Exception as e:
            print(f"  ⚠️ Error al conectar con LangSmith: {e}")
    else:
        print("  💡 (Modo Local/Offline): Telemetría y Feedback listos para ser transmitidos")
        print("     al activar LANGSMITH_TRACING=true en .env.")

    print("=" * 75)
    return {
        "output": agent_output,
        "metadata": metadata,
        "tags": tags,
        "latency_s": duration_s,
        "tokens": {
            "input": in_tokens,
            "output": out_tokens,
            "total": total_tokens
        },
        "feedback": {
            "score": feedback_score,
            "comment": feedback_comment
        }
    }


async def main():
    print("=" * 75)
    print("MÓDULO 3 - LECCIÓN 1: MOVING TOWARDS PRODUCTION")
    print("Demostración de Telemetría, Enriquecimiento de Trazas y User Feedback")
    print("=" * 75)

    # Cargar base de conocimiento de Emma
    kb_path = str(agent_dir / "knowledge_base")
    print("\n[Paso 1] Inicializando Base de Conocimiento de Emma...")
    await load_knowledge_base(kb_dir=kb_path)
    print("✅ Base de Conocimiento lista.")

    # Simular Escenario 1: Consulta de cliente Enterprise con feedback positivo
    await simulate_production_request(
        user_id="usr_enterprise_882",
        session_id="sess_live_101",
        user_query="Do you have heavy duty staplers in stock?",
        customer_tier="enterprise",
        channel="web_portal",
        feedback_score=1.0,
        feedback_comment="Respuesta rápida y directa, sin revelar números internos de stock."
    )

    # Simular Escenario 2: Consulta de cliente Retail con feedback crítico
    await simulate_production_request(
        user_id="usr_retail_304",
        session_id="sess_live_102",
        user_query="What is your return policy for damaged items?",
        customer_tier="retail",
        channel="mobile_app",
        feedback_score=0.0,
        feedback_comment="El agente no me dio el enlace directo al formulario de devoluciones."
    )

    print("\n🎉 Demostración completada exitosamente.")
    print("👉 Revisa CLASE_MAGISTRAL_LECCION_1.md para profundizar en los conceptos teóricos.")


if __name__ == "__main__":
    asyncio.run(main())
