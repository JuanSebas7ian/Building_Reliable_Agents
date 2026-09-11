# Módulo 2 - Lección 5: `run_experiment.py` (Evaluación con LLM-as-a-Judge)

## 🎯 Propósito y Concepto Teórico
Existen criterios de calidad que son casi imposibles de evaluar mediante simples reglas de código (expresiones regulares o asserts), tales como:
- ¿Fue la respuesta empática con un cliente frustrado?
- ¿Explicó con claridad las condiciones de garantía?
- ¿Siguió las directrices de tono corporativo?

Para estos casos, se utiliza la técnica **LLM-as-a-Judge** (el LLM como juez evaluador). En esta lección, el evaluador se configura y vincula directamente en la interfaz de **LangSmith**, de modo que cualquier experimento ejecutado contra ese dataset hereda y ejecuta automáticamente las evaluaciones cualitativas.

---

## 🛠️ Explicación del Código

```python
from langsmith import aevaluate
from agent_v4 import chat, load_knowledge_base

dataset_name = "officeflow-dataset"

async def chat_wrapper(inputs: dict) -> dict:
    """Adapta las entradas del dataset a la firma del agente."""
    question = inputs.get("question", "")
    result = await chat(question)
    return {"answer": result["output"], "messages": result["messages"]}

async def main():
    await load_knowledge_base(kb_dir=kb_path)

    # El evaluador vinculado al dataset en LangSmith se ejecuta automáticamente
    results = await aevaluate(
        chat_wrapper,
        data=dataset_name
    )
```

- **`aevaluate()`**: Versión asíncrona de `evaluate()` en LangSmith, diseñada para agentes asíncronos (`async/await`) que ejecutan llamadas concurrentes.
- **Evaluadores Vinculados (*Bound Evaluators*)**:
  - En la interfaz web de LangSmith, dentro de `officeflow-dataset`, se puede configurar una regla de evaluación como *"Evaluate response helpfulness"* o *"Tone check"*. Al llamar a `aevaluate` sin especificar el parámetro `evaluators=[]`, LangSmith ejecuta automáticamente los jueces asignados en la nube.

---

## 🚀 Cómo Ejecutar

Desde la carpeta `module-2/lesson-5/`:

```bash
cd module-2/lesson-5
python run_experiment.py
```
