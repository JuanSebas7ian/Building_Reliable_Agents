# Módulo 3 - Lección 3: Online Evals (Evaluaciones en Tiempo Real)

Esta lección cubre la arquitectura y ejecución práctica de **Online Evals**, evaluando trazas de producción de forma continua y asíncrona conforme llegan del tráfico real.

---

## 📁 Estructura de Archivos

* **[`online_evals.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/online_evals.py):** Pipeline completo de evaluación en streaming con evaluadores deterministas (política de stock y enrutamiento PRD), evaluadores heurísticos (concisión) y juez LLM (fidelidad contextual), compatible tanto en modo offline local como conectado a LangSmith.
* **[`eval_sentiment.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/eval_sentiment.py):** Evaluador de sentimientos del cliente y empatía del agente, capaz de operar 100% en local (sin API key de GPT) mediante análisis léxico o con Ollama local, y opcionalmente registrar el feedback en LangSmith.
* **[`CLASE_MAGISTRAL_LECCION_3.md`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/CLASE_MAGISTRAL_LECCION_3.md):** Guía conceptual exhaustiva sobre el trade-off latencia/coste, taxonomía piramidal de evaluadores y configuración en producción.

---

## 🚀 Cómo Ejecutar

### 1. Pipeline de Online Evals (Streaming)
```bash
uv run python module-3/lesson-3/online_evals.py
```

### 2. Evaluador de Sentimientos y Empatía (Local / LangSmith)
```bash
uv run python module-3/lesson-3/eval_sentiment.py
```
*(No requiere API key de GPT; utiliza análisis léxico o Ollama local `qwen2.5:7b`).*
