# Módulo 1 - Lección 2: `third_party_agent.py`

## 🎯 Propósito y Concepto Teórico
Este script demuestra cómo instrumentar con **LangSmith** un agente que utiliza **llamadas a funciones / herramientas (Tool Calling)** sin necesidad de utilizar el framework LangChain (es decir, usando directamente el SDK oficial de `openai`).

Muchas aplicaciones de producción prefieren construir sobre el SDK nativo de OpenAI o Anthropic. LangSmith permite instrumentar cualquier código Python mediante envoltorios de clientes y decoradores funcionales, ofreciendo trazabilidad completa e independiente del framework.

---

## 🛠️ Arquitectura del Código

1. **Envoltorio del Cliente (`wrap_openai`)**:
   ```python
   from openai import OpenAI
   from langsmith.wrappers import wrap_openai
   from langsmith import traceable

   client = wrap_openai(OpenAI())
   ```
   - Al envolver el cliente, todas las llamadas a `client.chat.completions.create` generan spans hijos de tipo `llm` dentro de la traza con metadatos de tokens, modelo (`gpt-5-nano`) y latencia.

2. **Decorador `@traceable(run_type="tool")`**:
   ```python
   @traceable(run_type="tool")
   def weather_retriever():
       """Retrieve current weather information."""
       return "It is sunny today"
   ```
   - Al marcar la función con `run_type="tool"`, LangSmith la etiqueta visualmente con un ícono de herramienta en la interfaz de usuario y registra los argumentos de entrada y la salida devuelta al modelo.

3. **Ciclo de Ejecución (Tool Execution Loop)**:
   - **Llamada 1**: Envía la pregunta del usuario (`"What is the weather today?"`) junto con el schema de `WEATHER_TOOL`.
   - **Decisión del Modelo**: El modelo responde con un `tool_calls` solicitando ejecutar `weather_retriever`.
   - **Ejecución Local**: El script intercepta la solicitud, ejecuta `weather_retriever()` y añade un mensaje con rol `tool`.
   - **Llamada 2**: Vuelve a invocar el LLM con el resultado de la herramienta para que formule la respuesta conversacional final.

---

## 🚀 Cómo Ejecutar

Desde la raíz de `Building_Releable_Agents`:

```bash
python module-1/lesson-2/third_party_agent.py
```

En la consola verás la respuesta final y en [LangSmith](https://smith.langchain.com/) podrás revisar el árbol de ejecución jerárquico.
