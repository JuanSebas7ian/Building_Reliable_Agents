"""
Script de validación rápida para verificar:
1. Conexión con Ollama local (chat y embeddings)
2. Carga del modelo qwen2.5:7b
3. Carga del modelo nomic-embed-text
4. Compatibilidad con OpenAI SDK (base_url="http://localhost:11434/v1")
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

print("=" * 60)
print("TEST DE INTEGRACIÓN: OLLAMA LOCAL + VENV")
print("=" * 60)
print(f"Base URL:         {BASE_URL}")
print(f"Chat Model:       {CHAT_MODEL}")
print(f"Embedding Model:  {EMBEDDING_MODEL}")
print("-" * 60)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# 1. Probar Embeddings
try:
    print(f"1. Probando generación de embeddings con '{EMBEDDING_MODEL}'...")
    emb_res = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input="Hola, probando embedding para Emma Agent"
    )
    dim = len(emb_res.data[0].embedding)
    print(f"   ✅ Embeddings OK (Dimensión vectorial: {dim})")
except Exception as e:
    print(f"   ❌ Error en embeddings: {e}")
    sys.exit(1)

# 2. Probar Chat Completion
try:
    print(f"2. Probando chat completion con '{CHAT_MODEL}'...")
    chat_res = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente técnico conciso."},
            {"role": "user", "content": "Di 'Hola Mundo, entorno listo' en una sola frase."}
        ],
        max_tokens=50
    )
    respuesta = chat_res.choices[0].message.content.strip()
    print(f"   ✅ Chat Completion OK")
    print(f"   Respuesta del modelo: \"{respuesta}\"")
except Exception as e:
    print(f"   ❌ Error en chat completion: {e}")
    sys.exit(1)

print("=" * 60)
print("🎉 ¡TODO EL ENTORNO Y OLLAMA ESTÁN OPERATIVOS AL 100%!")
print("=" * 60)
