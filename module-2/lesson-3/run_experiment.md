# Módulo 2 - Lección 3: `run_experiment.py` (Ejecución del Primer Experimento)

## 🎯 Propósito y Concepto Teórico
Este script enseña los fundamentos para orquestar un **Experimento Automatizado** en LangSmith utilizando la función de alto nivel `evaluate()`.

Un experimento en LangSmith conecta tres elementos esenciales:
1. **Target (Objetivo)**: La aplicación o función que procesa las entradas (en este ejemplo, una función simulada `dummy_app`).
2. **Dataset**: El conjunto de ejemplos con el que se pondrá a prueba el objetivo (`officeflow-dataset`).
3. **Evaluators**: Una lista de funciones de evaluación que puntúan la salida (en este caso, `mentions_officeflow`).

---

## 🛠️ Explicación del Código

```python
from dotenv import load_dotenv
from langsmith import evaluate

load_dotenv()

# 1. Función Target (Aplicación a evaluar)
def dummy_app(inputs: dict) -> dict:
    return {"response": "Sure! In OfficeFlow, you can reset your password from the settings page."}

# 2. Evaluador basado en código
def mentions_officeflow(outputs: dict) -> bool:
    return "officeflow" in outputs["response"].lower()

# 3. Lanzamiento del Experimento
results = evaluate(
    dummy_app,
    data="officeflow-dataset",
    evaluators=[mentions_officeflow]
)
```

- **`evaluate()`**:
  - Descarga automáticamente todos los ejemplos del dataset `officeflow-dataset` desde tu cuenta de LangSmith.
  - Ejecuta la función `dummy_app` para cada ejemplo.
  - Ejecuta cada función en `evaluators` pasando la salida producida.
  - Registra las puntuaciones (1 para `True`, 0 para `False`), estadísticas agregadas y enlaces al dashboard web de LangSmith.

---

## 🚀 Cómo Ejecutar

*(Nota: Asegúrate de haber subido previamente `officeflow-dataset` a LangSmith tal como se explica en [datasets_guide.md](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/datasets_guide.md))*.

Desde la carpeta `module-2/lesson-3/`:

```bash
cd module-2/lesson-3
python run_experiment.py
```

En la consola verás una barra de progreso interactiva y la URL directa para ver los resultados en la pestaña **Datasets & Testing** de LangSmith.
