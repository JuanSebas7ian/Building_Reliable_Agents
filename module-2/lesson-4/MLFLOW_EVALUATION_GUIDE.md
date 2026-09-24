# Guía de Evaluación de Agentes con MLflow (GenAI & Tracing)

> **Propósito**: Adaptación conceptual y técnica de la suite de evaluación determinista de la Lección 4 (LangSmith) al ecosistema de **MLflow** (versiones 2.14+ con soporte nativo de GenAI Evaluation y Tracing).  
> **Ubicación**: [`module-2/lesson-4/MLFLOW_EVALUATION_GUIDE.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/MLFLOW_EVALUATION_GUIDE.md)

---

## 🔄 1. Mapeo Arquitectónico: LangSmith vs. MLflow

Ambas plataformas comparten los mismos fundamentos de evaluación de agentes basados en LLM, pero utilizan nombres y primitivas distintas:

| Componente | Enfoque LangSmith (Lección 4) | Enfoque MLflow (GenAI) |
| :--- | :--- | :--- |
| **Dataset de Evaluación** | `officeflow-dataset` (Key-Value en la nube) | `pandas.DataFrame` cargado desde CSV o Delta Table |
| **Aplicación Target** | `run_agent(inputs: dict) -> dict` | Función callable `predict_fn(inputs_df)` o modelo PyFunc |
| **Evaluador Determinista** | Función `(run, example) -> {"score": ..., "comment": ...}` | Función envuelta en `mlflow.metrics.make_metric(...)` |
| **Evaluador LLM-Judge** | `evaluator create-llm` / Prompt Hub | `mlflow.metrics.genai.make_genai_metric(...)` |
| **Observabilidad / Tracing** | `@traceable` / `wrap_openai()` | Decorador `@mlflow.trace` o `mlflow.openai.autolog()` |
| **Orquestador Principal** | `langsmith.evaluate()` o `aevaluate()` | `mlflow.evaluate(model=..., data=..., extra_metrics=...)` |
| **Visualización** | Panel web [smith.langchain.com](https://smith.langchain.com) | Interfaz web local o remota (`mlflow ui`) |

---

## 📋 2. Catálogo de Prompts Adaptados para MLflow

Si estás interactuando con un asistente de IA para construir tu suite de pruebas en **MLflow**, estos son los prompts exactos que debes utilizar:

---

### 🔹 Prompt 1 - Evaluador de Política de Stock (Regex)

**Texto del prompt:**
> *"Crea una métrica personalizada para **MLflow Evaluation** utilizando `mlflow.metrics.make_metric` llamada `stock_policy_compliance`. Debe analizar la columna de predicciones generadas (`eval_df['prediction']`) usando expresiones regulares para verificar que el agente no exponga números exactos de existencias (ej. 'we have 45 pens'). Debe asignar una puntuación de 1.0 si utilizó bandas cualitativas ('in stock', 'running low') y 0.0 si filtró números de almacén, devolviendo un `MetricValue` con la justificación en `justifications` y el promedio en `aggregate_results`."*

---

### 🔹 Prompt 2 - Evaluador de Trayectoria SQL con MLflow Tracing

**Texto del prompt:**
> *"Diseña una métrica de evaluación en **MLflow** que audite la trayectoria de herramientas utilizando **MLflow Tracing** (`mlflow.get_trace`). Debe inspeccionar los spans de la traza para validar que cada vez que se invoque la función o span de `query_database`, el primer query ejecutado haya sido una consulta de esquema (`PRAGMA table_info` o `sqlite_master`) antes de lanzar cualquier `SELECT` de datos. Retorna score 1.0 si es conforme y 0.0 si intentó adivinar tablas."*

---

### 🔹 Prompt 3 - Wrapper del Agente (Run Function) con Aislamiento de Memoria

**Texto del prompt:**
> *"Diseña la función de inferencia `predict_fn(questions_df)` para ser evaluada con `mlflow.evaluate()`. Debe: (1) iterar sobre las filas del DataFrame, (2) aislar el `thread_id` en cada consulta para evitar contaminación de memoria conversacional en el agente Emma, (3) capturar la traza con el decorador `@mlflow.trace`, y (4) devolver una lista o Serie de Pandas con las respuestas finales generadas."*

---

### 🔹 Prompt 4 - Orquestación del Experimento Completo con `mlflow.evaluate()`

**Texto del prompt:**
> *"Escribe un script en Python que utilice **`mlflow.evaluate()`** para evaluar al agente Emma contra el archivo `officeflow-dataset.csv` convertido a Pandas DataFrame. El experimento debe: (1) abrir un run con `with mlflow.start_run(run_name='code-eval-v5-mlflow'):`, (2) pasar la función del agente en `model`, (3) incluir las métricas personalizadas `stock_policy_metric` y `schema_check_metric` en `extra_metrics`, y (4) registrar los resultados en el tracking server de MLflow."*

---

### 🔹 Prompt 5 - Auditoría y Búsqueda de Infracciones con `MlflowClient`

**Texto del prompt:**
> *"Usa **`mlflow.client.MlflowClient`** para buscar en nuestro experimento de MLflow todos los runs donde la métrica `stock_policy_compliance` o `schema_before_query` sea igual a 0.0. Imprime en consola la pregunta del cliente, la respuesta de Emma y la justificación del fallo registrada en los artefactos de evaluación."*

---

## 💻 3. Código de Implementación Completo para MLflow

A continuación tienes el código Python equivalente a [`run_eval.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/run_eval.py) implementado nativamente con la API de MLflow:

```python
"""
run_eval_mlflow.py - Evaluación de Agentes con MLflow GenAI & Tracing
Equivalente de la Lección 4 de LangSmith adaptado a MLflow
"""
import asyncio
import re
import uuid
import pandas as pd
import mlflow
from mlflow.metrics import make_metric, MetricValue

# 1. Definición de la Métrica Determinista de Stock en MLflow
EXACT_QUANTITY_PATTERNS = [
    r"\b(?:we have|there are|currently have|in stock[:\s]+|left[:\s]+|have)\s*\d+\s*(?:units|reams|items|boxes|packs|pens|notebooks)?\b",
    r"\b\d+\s+(?:units|reams|items|boxes|packs|pens|notebooks)\s+(?:in stock|available|left)\b",
    r"\bexact(?:ly)?\s+\d+\b",
]

def eval_stock_fn(eval_df: pd.DataFrame, builtin_metrics: dict) -> MetricValue:
    """Evalúa si las predicciones respetan la confidencialidad de inventario."""
    scores = []
    justifications = []

    for pred in eval_df["prediction"]:
        text = str(pred).lower()
        violations = []
        for pattern in EXACT_QUANTITY_PATTERNS:
            matches = re.findall(pattern, text, re.I)
            if matches:
                violations.extend(matches)

        if violations:
            scores.append(0.0)
            justifications.append(f"Infracción detectada: {', '.join(violations)}")
        else:
            scores.append(1.0)
            justifications.append("Cumple política de stock con bandas cualitativas.")

    mean_score = sum(scores) / len(scores) if scores else 1.0
    return MetricValue(
        scores=scores,
        justifications=justifications,
        aggregate_results={"mean": mean_score},
    )

stock_policy_metric = make_metric(
    eval_fn=eval_stock_fn,
    greater_is_better=True,
    name="stock_policy_compliance",
)

# 2. Wrapper del Agente para MLflow con Aislamiento de Memoria
import agent_v5
from agent_v5 import chat

def predict_fn(questions_df: pd.DataFrame) -> list:
    """
    Función de inferencia consumida por mlflow.evaluate().
    Genera un thread_id fresco por fila para aislar la memoria conversacional.
    """
    predictions = []
    # Determinar el nombre de la columna que contiene la pregunta
    col = "question" if "question" in questions_df.columns else questions_df.columns[0]

    for question in questions_df[col]:
        # Aislamiento de sesión idéntico a LangSmith
        agent_v5.thread_id = str(uuid.uuid4())
        result = asyncio.run(chat(str(question)))
        predictions.append(result.get("output", ""))

    return predictions

# 3. Lanzamiento del Experimento con mlflow.evaluate()
if __name__ == "__main__":
    mlflow.set_experiment("officeflow-agent-evaluation")

    # Cargar dataset de prueba
    dataset_path = "module-2/lesson-2/officeflow-dataset.csv"
    df = pd.read_csv(dataset_path)

    print("Iniciando evaluación con MLflow...")
    with mlflow.start_run(run_name="code-eval-v5-mlflow"):
        eval_results = mlflow.evaluate(
            model=predict_fn,
            data=df,
            targets=None,  # Evaluación de respuesta abierta sin ground truth estático
            model_type="question-answering",
            extra_metrics=[stock_policy_metric],
        )

        print("\n" + "=" * 60)
        print("MÉTRICAS OBTENIDAS EN MLFLOW:")
        for metric_name, val in eval_results.metrics.items():
            print(f" - {metric_name}: {val * 100:.1f}%")
        print("=" * 60)
        print("Para ver los resultados interactivos ejecuta: mlflow ui")
```

---

## 🖥️ 4. Cómo Visualizar los Resultados en la Interfaz de MLflow

1. **Instalar dependencias necesarias:**

   ```bash
   pip install mlflow pandas
   ```

2. **Ejecutar la evaluación:**

   ```bash
   python run_eval_mlflow.py
   ```

3. **Abrir la interfaz visual de MLflow:**

   ```bash
   mlflow ui --port 5000
   ```

4. Navega a `http://localhost:5000` en tu navegador.
5. Selecciona el experimento **`officeflow-agent-evaluation`**:
   - Podrás ver la tabla comparativa de runs con las columnas `stock_policy_compliance`.
   - En la pestaña **Artifacts** -> **`eval_results_table.json`** tendrás la matriz completa con la pregunta de entrada, la predicción de Emma y la justificación del evaluador.

---

## 📚 Catálogo de Skills Oficiales de MLflow

Para conocer los 13 skills oficiales de MLflow disponibles para Antigravity y sus comandos de instalación, consulta:  
👉 [`MLFLOW_SKILLS_CATALOG.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/MLFLOW_SKILLS_CATALOG.md)
