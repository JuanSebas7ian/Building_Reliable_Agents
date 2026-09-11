# Agente OfficeFlow: `agent_v1.py` (+ LangSmith Tracing)

## 🎯 Propósito y Contexto
`agent_v1.py` da el paso fundamental en el Módulo 1 (Observabilidad): **convertir el agente de una caja negra en un sistema totalmente observable**. Aquí se añade la instrumentación con **LangSmith**, lo que permite inspeccionar la ejecución completa en la plataforma de LangChain.

---

## 🔄 Cambios Respecto a `agent_v0.py`

1. **Envoltura del Cliente OpenAI con `wrap_openai`**:
   ```python
   from langsmith.wrappers import wrap_openai
   client = wrap_openai(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))
   ```
   - Intercepta automáticamente todas las llamadas a la API de OpenAI, registrando inputs, outputs, parámetros (`model`, `temperature`), tokens consumidos (prompt tokens, completion tokens) y tiempo de respuesta.

2. **Identificador Único de Hilo con `uuid7`**:
   ```python
   from langsmith import uuid7
   thread_id = str(uuid7())
   ```
   - Cada conversación ahora tiene un ID único ordenado cronológicamente (`UUIDv7`), permitiendo rastrear la evolución del contexto conversacional en LangSmith.

3. **Decorador `@traceable` en Herramientas y Función Principal**:
   - En la herramienta SQL:
     ```python
     @traceable(name="query_database", run_type="tool")
     def query_database(query: str, db_path: str) -> str:
     ```
   - En la herramienta de búsqueda semántica:
     ```python
     @traceable(name="search_knowledge_base", run_type="tool")
     async def search_knowledge_base(query: str, top_k: int = 2) -> str:
     ```
   - En el punto de entrada del agente:
     ```python
     @traceable(name="Emma", metadata={"thread_id": thread_id})
     async def chat(question: str) -> dict:
     ```

4. **Retorno Estructurado**:
   - Retorna un diccionario con `{ "messages": messages, "output": final_content }`, permitiendo que evaluadores externos analicen tanto el resultado como el historial de mensajes de la interacción.

---

## 🔍 ¿Qué Permite Analizar en LangSmith?

Al enviar un mensaje al agente en `agent_v1.py`, se genera un **Trace** en tu proyecto de LangSmith (`lca-reliable-agents`):
- **Árbol de Ejecución (Run Tree)**:
  - `Emma` (Root Run, tipo `chain`)
    - `ChatCompletion` (Llamada inicial al LLM para decidir si usar herramientas)
    - `query_database` o `search_knowledge_base` (Span de tipo `tool`)
    - `ChatCompletion` (Segunda llamada al LLM con los resultados de la herramienta para redactar la respuesta final)
- **Diagnóstico Inmediato**: Se puede comprobar si el modelo generó una consulta SQL inválida o qué similitud de coseno obtuvieron los chunks en el RAG.

---

## 🚀 Cómo Ejecutar

```bash
cd officeflow-agent
python agent_v1.py
```

Luego, ingresa a [https://smith.langchain.com/](https://smith.langchain.com/), selecciona el proyecto `lca-reliable-agents` y observa la traza generada en tiempo real.
