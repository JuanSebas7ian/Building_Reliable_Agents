# Módulo 3 - Lección 4: Automations (Automatizaciones y el Data Flywheel)

Esta lección enseña a configurar y ejecutar **reglas de automatización reactivas** sobre el flujo de trazas en vivo, cerrando el ciclo virtuoso de mejora continua (**The Data Flywheel**).

---

## 📁 Estructura de Archivos

* **[`automations_pipeline.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-4/automations_pipeline.py):** Motor ejecutor de reglas de automatización (detección de violaciones de políticas, feedback negativo y brechas de SLA), auto-etiquetado, alertas webhook y exportación automática a datasets de regresión.
* **[`CLASE_MAGISTRAL_LECCION_4.md`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-4/CLASE_MAGISTRAL_LECCION_4.md):** Guía teórica y práctica completa sobre la arquitectura del Data Flywheel, diseño de triggers/actions y prevención de fatiga de alertas.

---

## 🚀 Cómo Ejecutar

Ejecuta la demostración del motor de automatizaciones:

```bash
uv run python module-3/lesson-4/automations_pipeline.py
```

El script evaluará 4 trazas representativas de producción (éxito, fuga de inventario, alucinación con feedback negativo y latencia degradada), disparará las acciones correspondientes e ilustrará la curación automática del dataset `production-regressions`.
