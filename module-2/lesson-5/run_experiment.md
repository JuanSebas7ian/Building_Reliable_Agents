# Módulo 2 - Lección 5: `run_experiment.py` (Evaluación con LLM-as-a-Judge)

## 🎯 Propósito y Concepto Teórico
Existen criterios de calidad subjetivos que son casi imposibles de evaluar mediante simples reglas de código (expresiones regulares o asserts), tales como:
- ¿Fue la respuesta empática con un cliente frustrado?
- ¿Explicó con claridad y sin rodeos las condiciones de garantía?
- ¿Siguió las directrices de tono corporativo y amabilidad?

Para estos casos, se utiliza la técnica **LLM-as-a-Judge** (el LLM como juez evaluador).

En esta lección implementamos dos modalidades complementarias:
1. **Juez en Código Local/Cloud ([`eval_llm_judge.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/eval_llm_judge.py))**: Ejecuta un LLM local (`qwen2.5:7b` en Ollama) o cloud (OpenAI) con una rúbrica en formato JSON estructurado sin costo adicional de API.
2. **Juez Vinculado en la Nube (*Bound Evaluator*)**: Configurable desde la UI de LangSmith en la sección de evaluadores de datasets.

---

## 🛠️ Arquitectura del Juez Local

El script [`eval_llm_judge.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/eval_llm_judge.py) implementa la función `helpfulness_and_tone_judge`:
- Prompt con criterios explícitos:
  1. **Helpfulness**: ¿Respondió con precisión a la consulta?
  2. **Tone & Empathy**: ¿Fue educado y empático?
  3. **Policy Compliance**: ¿Redirigió al correo correcto si no puede resolverlo?
- Salida estructurada JSON con `score` (1 a 5) y `reasoning`.

---

## 🚀 Cómo Ejecutar

Desde la carpeta raíz del proyecto:

```bash
uv run python module-2/lesson-5/run_experiment.py
```

Para probar solo el evaluador LLM de forma aislada:
```bash
uv run python module-2/lesson-5/eval_llm_judge.py
```
