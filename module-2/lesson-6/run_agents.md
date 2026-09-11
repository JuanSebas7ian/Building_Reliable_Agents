# Módulo 2 - Lección 6: `run_agents.py` (Ejecución Previa para Evaluación Pareada)

## 🎯 Propósito y Concepto Teórico
La **Evaluación Pareada (Pairwise Evaluation / Test A/B)** compara las salidas de dos modelos o dos versiones de un agente (`v4` vs `v5`) frente a las mismas preguntas para determinar cuál de los dos ofrece un mejor rendimiento según un criterio específico (en este caso: **concisión y claridad**).

El primer paso de un flujo pareado consiste en ejecutar ambas versiones sobre el dataset completo y registrar los resultados como dos experimentos independientes en LangSmith.

---

## 🛠️ Arquitectura del Script

1. **Definición de Wrappers de Ejecución**:
   - `chat_wrapper_v4`: Invoca `agent_v4.chat()`.
   - `chat_wrapper_v5`: Invoca `agent_v5.chat()`.

2. **Ejecución Asíncrona Concurrente con `aevaluate`**:
   ```python
   v4_results = await aevaluate(
       chat_wrapper_v4,
       data=DATASET_NAME,
       experiment_prefix="agent-v4",
   )

   v5_results = await aevaluate(
       chat_wrapper_v5,
       data=DATASET_NAME,
       experiment_prefix="agent-v5",
   )
   ```

3. **Salida**:
   - Imprime los nombres de los dos experimentos creados en LangSmith (por ejemplo: `agent-v4-7a3b` y `agent-v5-9c1d`), los cuales servirán como entrada para el evaluador pareado.

---

## 🚀 Cómo Ejecutar

Desde la carpeta `module-2/lesson-6/`:

```bash
cd module-2/lesson-6
python run_agents.py
```
