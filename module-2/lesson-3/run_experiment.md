# Módulo 2 - Lección 3: `run_experiment.py` (Ejecución de Experimentos en LangSmith)

## 🎯 Propósito y Concepto Teórico

Este script enseña los fundamentos para orquestar un **Experimento Automatizado** en LangSmith utilizando la función de alto nivel `evaluate()` (o `aevaluate()` para flujos asíncronos).

Un experimento en LangSmith conecta tres elementos esenciales:
1. **Target (Objetivo)**: La aplicación o función que procesa las entradas (`dummy_app` pedagógica o el agente real `emma_agent_app`).
2. **Dataset**: El conjunto de ejemplos con el que se pondrá a prueba el objetivo (`officeflow-dataset`).
3. **Evaluators**: Lista de funciones de evaluación que puntúan la salida (`mentions_officeflow` y `token_efficiency_check`).

---

## 🛠️ Explicación de los Componentes

### 1. Targets Disponibles
- **`dummy_app(inputs)`**: Función síncrona mínima y rápida para entender la mecánica de `evaluate()` sin costo computacional.
- **`emma_agent_app(inputs)`**: Función asíncrona que invoca a Emma (`agent_v5`) creando un nuevo `thread_id` aislado para cada consulta, conectándose a Ollama local (`qwen2.5:7b`) o OpenAI.

### 2. Evaluadores Basados en Código
- **`mentions_officeflow`**: Valida que la respuesta mencione la marca OfficeFlow.
- **`token_efficiency_check`**: Utiliza `token_utils.py` para medir el tamaño de la respuesta en tokens, premiando la concisión (respuestas $\le$ 120 tokens).

### 3. Lanzamiento del Experimento
```python
results = evaluate(
    dummy_app,
    data="officeflow-dataset",
    evaluators=[mentions_officeflow, token_efficiency_check],
    experiment_prefix="dummy-app-experiment"
)
```

- **`evaluate()` / `aevaluate()`**:
  - Descarga automáticamente los ejemplos de `officeflow-dataset` desde LangSmith.
  - Ejecuta el target para cada ejemplo.
  - Ejecuta cada evaluador y envía las puntuaciones a LangSmith.
  - Muestra en consola una barra de progreso y la URL directa del experimento.

---

## 🚀 Cómo Ejecutar

*(Nota: Asegúrate de haber subido previamente `officeflow-dataset` ejecutando `uv run python module-2/lesson-2/upload_dataset.py`)*.

### Opción A: Prueba Rápida con `dummy_app`
```bash
uv run python module-2/lesson-3/run_experiment.py --mode dummy
```

### Opción B: Experimento Completo con el Agente Emma Real
```bash
uv run python module-2/lesson-3/run_experiment.py --mode agent
```
