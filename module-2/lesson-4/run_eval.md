# Módulo 2 - Lección 4: `run_eval.py` (Lanzador de Evaluación de Esquema)

## 🎯 Propósito
Este script es el ejecutor (*runner*) que conecta el agente de producción [`agent_v5.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v5.py), el dataset [`officeflow-dataset`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/officeflow-dataset.csv) y el evaluador determinista [`eval_schema_check.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_schema_check.py).

---

## 🛠️ Arquitectura del Script

1. **Aislamiento de Sesiones por Ejemplo**:
   ```python
   def run_agent(inputs: dict) -> dict:
       agent_v5.thread_id = str(uuid7())
       return asyncio.run(chat(inputs["question"]))
   ```
   - Para evitar que la memoria conversacional de una pregunta interfiera con la siguiente, se genera un nuevo `thread_id` en cada iteración del dataset.

2. **Carga Previa de la Base de Conocimiento**:
   ```python
   await setup()  # Carga embeddings y documentos en memoria antes del test
   ```

3. **Ejecución con Prefijo de Experimento**:
   ```python
   results = evaluate(
       run_agent,
       data="officeflow-dataset",
       evaluators=[schema_before_query],
       experiment_prefix="schema-check-v5",
   )
   ```
   - `experiment_prefix="schema-check-v5"` ayuda a etiquetar y comparar distintas ejecuciones en LangSmith.

---

## 🚀 Cómo Ejecutar

Desde la carpeta `module-2/lesson-4/`:

```bash
cd module-2/lesson-4
python run_eval.py
```

Al terminar, obtendrás una tasa de éxito (porcentaje de consultas donde se respetó el chequeo previo de esquema) y podrás filtrar en LangSmith qué preguntas fallaron para investigar el motivo.
