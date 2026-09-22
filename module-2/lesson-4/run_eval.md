# Módulo 2 - Lección 4: `run_eval.py` (Lanzador de Evaluaciones Basadas en Código)

## 🎯 Propósito
Este script es el ejecutor (*runner*) que conecta el agente de producción [`agent_v5.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v5.py), el dataset [`officeflow-dataset`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/officeflow-dataset.csv) y la suite de evaluadores deterministas basados en código:
1. [`eval_schema_check.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_schema_check.py): Descubrimiento previo del esquema SQL.
2. [`eval_stock_policy.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_stock_policy.py): Cumplimiento estricto de no exponer números exactos de existencias.

---

## 🛠️ Arquitectura del Script

1. **Aislamiento de Sesiones por Ejemplo**:
   ```python
   def run_agent(inputs: dict) -> dict:
       agent_v5.thread_id = str(uuid7())
       return asyncio.run(chat(inputs["question"]))
   ```
   - Para evitar que la memoria conversacional de una pregunta contamine la siguiente, se genera un nuevo `thread_id` (UUIDv7) en cada iteración del dataset.

2. **Carga Previa de la Base de Conocimiento**:
   ```python
   await setup()  # Carga embeddings y documentos en memoria antes del test
   ```

3. **Ejecución de Múltiples Evaluadores**:
   ```python
   results = evaluate(
       run_agent,
       data="officeflow-dataset",
       evaluators=[schema_before_query, check_no_exact_quantities],
       experiment_prefix="code-eval-v5",
   )
   ```

---

## 🚀 Cómo Ejecutar

Desde la raíz del proyecto o desde la carpeta `module-2/lesson-4/`:

```bash
uv run python module-2/lesson-4/run_eval.py
```

Al terminar, obtendrás métricas objetivas (100% deterministas, sin costo de tokens por evaluación) y la URL directa para examinar en LangSmith los casos específicos que no cumplieron las políticas.

---

## 📚 Documentación y Catálogo de Prompts

- 📖 **Guía Completa de la Lección**: [`LESSON_4_COMPLETE_GUIDE.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/LESSON_4_COMPLETE_GUIDE.md)
- 💬 **Catálogo de Prompts para Skills**: [`SKILLS_PROMPTS_GUIDE.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/SKILLS_PROMPTS_GUIDE.md)
