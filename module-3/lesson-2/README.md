# Módulo 3 - Lección 2: Insights Agent (Análisis de Trazas a Escala)

Esta lección aborda el desafío de la observabilidad cuando un agente atiende cientos o miles de consultas al día en producción.

---

## 📂 Contenido de la Lección

| Archivo | Descripción |
| :--- | :--- |
| [`CLASE_MAGISTRAL_LECCION_2.md`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-2/CLASE_MAGISTRAL_LECCION_2.md) | **Guía pedagógica completa**: Propósito del Insights Agent, la falacia de la revisión manual, arquitectura de time-shifting, métricas agregadas y hallazgos reales. |
| [`insights_agent.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-2/insights_agent.py) | **Agente analista ejecutable**: Procesa `synthetic_traces.json`, calcula latencias (p50/p90/p99) y ejecuta el LLM para extraer intenciones, fallos y recomendaciones. |
| [`upload_traces.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-2/upload_traces.py) | **Script de ingesta masiva**: Sube las 1,000 trazas a LangSmith proyectando las fechas al momento presente mediante *time-shifting* dinámico. |
| [`generate_traces.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-2/generate_traces.py) | **Generador sintético**: Código que construyó las 3,740 ejecuciones de simulación de producción. |
| [`synthetic_traces.json`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-2/synthetic_traces.json) | **Dataset masivo**: 1,000 trazas completas de producción de OfficeFlow. |

---

## 🚀 Cómo Ejecutar

1. **Ejecutar el Insights Agent**:
   ```bash
   uv run python module-3/lesson-2/insights_agent.py --sample-size 20
   ```

2. **Subir las trazas a LangSmith (opcional si tienes API Key)**:
   ```bash
   uv run python module-3/lesson-2/upload_traces.py --project lca-reliable-agents
   ```
