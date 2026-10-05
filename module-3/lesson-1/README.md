# Módulo 3 - Lección 1: Moving Towards Production

Esta lección marca el inicio del **Módulo 3: Moving Towards Production**, donde abordamos la transición crítica desde las pruebas controladas en el laboratorio (datasets y evaluación offline) hacia la operación con usuarios reales en entornos de producción.

---

## 📂 Contenido de la Lección

| Archivo | Descripción |
| :--- | :--- |
| [`CLASE_MAGISTRAL_LECCION_1.md`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-1/CLASE_MAGISTRAL_LECCION_1.md) | **Guía pedagógica completa**: Comparativa offline vs. online, los 4 pilares de producción (Telemetría rica, User Feedback, Muestreo y Data Flywheel) con diagramas Mermaid. |
| [`production_telemetry.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-1/production_telemetry.py) | **Script práctico de demostración**: Invocación instrumentada con metadatos contextuales (`user_id`, `session_id`, `environment`, `release`), métricas de tokens/latencia y simulación de registro de retroalimentación de usuario (👍/👎). |

---

## 🚀 Cómo Ejecutar la Demostración

Para ejecutar la simulación de telemetría de producción:

```bash
uv run python module-3/lesson-1/production_telemetry.py
```

El script simulará dos llamadas al agente Emma v5 bajo tráfico de producción (un cliente *Enterprise* con feedback positivo y un cliente *Retail* con feedback de mejora), calculando la latencia exacta y tokens consumidos.
