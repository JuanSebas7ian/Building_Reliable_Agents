# Módulo 3 - Lección 3: Online Evals (Evaluaciones en Tiempo Real)

Esta lección cubre la arquitectura y ejecución práctica de **Online Evals**, evaluando trazas de producción de forma continua y asíncrona conforme llegan del tráfico real.

---

## 📁 Estructura de Archivos

* **[`online_evals.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/online_evals.py):** Pipeline completo de evaluación en streaming con evaluadores deterministas (política de stock y enrutamiento PRD), evaluadores heurísticos (concisión) y juez LLM (fidelidad contextual), compatible tanto en modo offline local como conectado a LangSmith.
* **[`CLASE_MAGISTRAL_LECCION_3.md`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/CLASE_MAGISTRAL_LECCION_3.md):** Guía conceptual exhaustiva sobre el trade-off latencia/coste, taxonomía piramidal de evaluadores y configuración en producción.

---

## 🚀 Cómo Ejecutar

Ejecuta el pipeline de evaluación en streaming:

```bash
uv run python module-3/lesson-3/online_evals.py
```

El script analizará tres trazas sintéticas de producción en tiempo real e imprimirá el veredicto y métricas para cada una, registrando feedback en LangSmith si las credenciales están configuradas.
