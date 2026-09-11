# Verificador de Entorno: `env_utils.py`

## 🎯 Objetivo
El script `env_utils.py` es una utilidad de diagnóstico automatizada diseñada por LangChain Academy para verificar que tu entorno de ejecución local cumple con todos los requisitos necesarios para completar el curso **Building Reliable Agents** de manera fiable.

---

## 🔍 ¿Qué verifica este script?

1. **Versión de Python**:
   - Comprueba que la versión de Python sea mayor o igual a **3.12** y menor o igual a **3.13** (`>=3.12, <=3.13`).
   - Muestra la ruta del ejecutable de Python activo para confirmar si estás en un entorno virtual (`.venv`).

2. **Detección de Entorno Virtual**:
   - Valida si estás ejecutando el script dentro de un virtualenv (`VIRTUAL_ENV` o `sys.prefix != sys.base_prefix`).

3. **Instalación y Versión de Paquetes Clave**:
   - `openai`: SDK de OpenAI para invocar modelos como `gpt-5-nano` y modelos de embedding.
   - `langsmith`: Cliente y decoradores para instrumentación y evaluación.
   - `langsmith-fetch`: Utilidad de sincronización de trazas.
   - `python-dotenv`: Carga de variables de entorno desde `.env`.
   - `numpy`: Cálculos de similitud coseno en búsqueda vectorial RAG.
   - `anthropic` (opcional): Evaluadores basados en Claude.

4. **Variables de Entorno y Claves de API**:
   - `OPENAI_API_KEY`: Requerida para que los agentes y evaluadores interactúen con LLMs.
   - `LANGSMITH_API_KEY`: Requerida para enviar trazas y registrar experimentos.
   - `LANGSMITH_TRACING`: Debe estar configurada en `true`.
   - `LANGSMITH_PROJECT`: Proyecto de LangSmith destino (por defecto `lca-reliable-agents`).
   - Detecta **conflictos de variables de entorno** (si una variable está configurada a nivel de sistema operativo y difiere del archivo `.env`).

---

## 🚀 Cómo Ejecutar

Desde la raíz de la carpeta `Building_Releable_Agents`:

```bash
# Con uv (recomendado)
uv run python env_utils.py

# O con python estándar (activando previamente tu entorno virtual)
python env_utils.py
```

---

## 📋 Interpretación de Resultados

- **✅ PASS (Verde)**: La comprobación fue exitosa.
- **⚠️ WARNING (Amarillo)**: Advertencia (por ejemplo, clave de Anthropic ausente si no vas a usar modelos de Anthropic).
- **❌ FAIL (Rojo)**: Fallo crítico. Debes corregir la configuración antes de continuar (por ejemplo, falta de `OPENAI_API_KEY` o versión incompatible de Python).
