# Módulo 2 - Lección 6: `run_pairwise_experiment.py` (Experimento Pareado Completo)

## 🎯 Propósito
Este script ejecuta de principio a fin el flujo completo de evaluación pareada A/B entre **Emma v4** y **Emma v5**:
1. Ejecuta el agente v4 sobre las 25 preguntas del dataset.
2. Ejecuta el agente v5 sobre las mismas 25 preguntas.
3. Invoca la evaluación pareada en LangSmith barajando el orden para evitar sesgos (`randomize_order=True`).
4. Genera una tabla comparativa de victorias (Win-Rate) para determinar qué versión de agente es superior.

---

## 🛠️ Explicación del Código

```python
# Paso 1 y 2: Ejecución de ambas versiones
v4_results = await aevaluate(chat_wrapper_v4, data=DATASET_NAME, experiment_prefix="agent-v4")
v5_results = await aevaluate(chat_wrapper_v5, data=DATASET_NAME, experiment_prefix="agent-v5")

v4_experiment = v4_results.experiment_name
v5_experiment = v5_results.experiment_name

# Paso 3: Comparación Pareada con Randomización
evaluate(
    (v4_experiment, v5_experiment),
    evaluators=[conciseness_evaluator],
    randomize_order=True,
)
```

---

## 📊 Visualización de Resultados en LangSmith
Al acceder a la interfaz de LangSmith, podrás ver:
- El gráfico de barras con el porcentaje de victorias: `agent_v5` vs `agent_v4`.
- La justificación del juez LLM en cada fila individual explicando por qué la versión concisa resolvió la duda del cliente más eficientemente.

---

## 🚀 Cómo Ejecutar

Desde la carpeta `module-2/lesson-6/`:

```bash
cd module-2/lesson-6
python run_pairwise_experiment.py
```
*(Nota: Este script ejecutará 25 llamadas para v4, 25 para v5 y 25 evaluaciones con el juez, por lo que tardará aproximadamente 1 a 2 minutos).*
