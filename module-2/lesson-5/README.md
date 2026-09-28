# Módulo 2 - Lección 5: Evaluación Cualitativa con LLM-as-a-Judge

> **Curso Oficial**: [LangChain Academy - Building Reliable Agents: Lesson 5 - Eval 2: LLM-as-Judge](https://academy.langchain.com/courses/take/building-reliable-agents/multimedia/72670191-lesson-5-eval-2-llm-as-judge)  
> **Guía Pedagógica Maestra**: [`LESSON_5_COMPLETE_GUIDE.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/LESSON_5_COMPLETE_GUIDE.md)  
> **Skills de Antigravity Integrados**: [`langsmith-evaluator`](file:///f:/Cursos_code/LANGCHAIN/.agents/skills/langsmith-evaluator/SKILL.md) & [`langsmith-trace`](file:///f:/Cursos_code/LANGCHAIN/.agents/skills/langsmith-trace/SKILL.md)  

---

## 🤖 Modelos de Inteligencia Artificial Utilizados

Esta lección opera de forma autónoma, privada y con costo $0 en tu máquina local a través de **Ollama**:

| Componente | Modelo | Endpoint | Tipo / Formato | Función en la Lección |
| :--- | :--- | :--- | :--- | :--- |
| **LLM Juez (*Judge*)** | `qwen2.5:7b` | `http://localhost:11434/v1` | 7.6B Parámetros (Q4_K_M) | Evalúa tono, empatía, utilidad y apego a políticas corporativas mediante rúbrica 1-5 |
| **Agente Evaluado (Emma v4)** | `qwen2.5:7b` | `http://localhost:11434/v1` | Temperature: 0.1 | Genera la respuesta al cliente resolviendo consultas SQL y RAG |
| **Modelo de Embeddings** | `nomic-embed-text` | `http://localhost:11434/api/embeddings` | 768 dimensiones | Embebido vectorial de los documentos de políticas de OfficeFlow (`knowledge_base`) |

> [!NOTE]
> Si deseas alternar a **OpenAI** en la nube, basta con configurar en `.env`:
> `CHAT_MODEL=gpt-5-nano` y `EMBEDDING_MODEL=text-embedding-3-small`.

---

## 🎯 ¿Qué es LLM-as-a-Judge y por qué lo necesitamos?

En la [Lección 4](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/LESSON_4_COMPLETE_GUIDE.md), construimos evaluadores deterministas basados en código Python (expresiones regulares y validación de esquemas SQL). Estos evaluadores son perfectos para reglas rígidas:
* ✅ No revelar el número exacto de existencias en el almacén.
* ✅ Verificar que se consulte `PRAGMA table_info` antes de lanzar un `SELECT`.

Sin embargo, el código tradicional **no puede evaluar cualidades humanas y subjetivas**:
* ¿Fue la respuesta de Emma genuinamente empática ante un cliente molesto?
* ¿Explicó las políticas de garantía de forma comprensible o sonó como un robot insensible?
* ¿Proporcionó el canal de escalado correcto (`returns@officeflow.com`) si no podía resolver la solicitud directamente?

El patrón **LLM-as-a-Judge** utiliza un modelo de lenguaje para auditar las interacciones de otro agente según una rúbrica estructurada.

---

## 📂 Archivos de la Lección 5

| Archivo | Documentación | Rol en la Arquitectura |
| :--- | :--- | :--- |
| [`eval_llm_judge.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/eval_llm_judge.py) | [`eval_llm_judge.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/eval_llm_judge.md) | Función evaluadora `helpfulness_and_tone_judge`: Prompt con rúbrica 1-5, JSON estructurado y reasoning-first CoT |
| [`run_experiment.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/run_experiment.py) | [`run_experiment.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/run_experiment.md) | Orquestador asíncrono que corre a Emma (`agent_v4.py`) sobre `officeflow-dataset` (25 preguntas) y registra las trazas y scores en LangSmith |
| [`LESSON_5_COMPLETE_GUIDE.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/LESSON_5_COMPLETE_GUIDE.md) | - | Guía teórica magistral completa con diagramas Mermaid, mitigación de sesgos cognitivos y análisis de calibración |

---

## 🚀 Guía Rápida de Ejecución

### 1. Prueba Unitaria Diagnóstica (Sin costo, validación inmediata con Ollama)

Ejecuta el evaluador de forma aislada contra dos casos sintéticos (uno de excelente atención y otro deficiente):

```bash
uv run python module-2/lesson-5/eval_llm_judge.py
```

### 2. Ejecutar el Experimento Completo en LangSmith

Ejecuta a Emma v4 sobre las 25 preguntas del dataset corporativo y califica cada respuesta con el juez LLM:

```bash
uv run python module-2/lesson-5/run_experiment.py
```

> [!TIP]
> En [`run_experiment.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/run_experiment.py) se fijó `max_concurrency=1` para asegurar estabilidad térmica y evitar contención en la VRAM de tu GPU local durante la inferencia secuencial de Ollama.
