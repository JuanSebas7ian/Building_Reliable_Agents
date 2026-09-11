# Módulo 1 - Lección 2: `thread_agent.py`

## 🎯 Propósito y Concepto Teórico
Este script enseña cómo gestionar el **estado conversacional (threads o hilos)** y asociar cada turno de diálogo a un mismo identificador único visible y filtrable en **LangSmith**.

En sistemas conversacionales reales, los agentes deben recordar turnos anteriores. Al instrumentar con LangSmith, asociar un `thread_id` en los metadatos de la traza permite agrupar todas las interacciones de un usuario a lo largo del tiempo.

---

## 🛠️ Arquitectura del Código

1. **Generación de ID con `uuid7`**:
   ```python
   from langsmith import traceable, uuid7
   THREAD_ID = str(uuid7())
   ```
   - `uuid7` genera identificadores únicos con orden temporal integrado (timestamp en los primeros bits), lo que permite que las trazas aparezcan ordenadas cronológicamente en la base de datos de LangSmith.

2. **Almacenamiento de Memoria (`thread_store`)**:
   - Diccionario en memoria que simula la base de datos de sesiones:
     ```python
     thread_store: dict[str, list] = {}
     ```

3. **Metadatos en el Decorador `@traceable`**:
   ```python
   @traceable(name="Name Agent", metadata={"thread_id": THREAD_ID})
   def chat_pipeline(messages: list):
   ```
   - El argumento `metadata={"thread_id": THREAD_ID}` etiqueta el Run. En LangSmith puedes filtrar fácilmente: `metadata.thread_id == "..."` para ver la sesión completa.

4. **Flujo de Prueba Multi-Turno**:
   - Mensaje 1: *"Hi, my name is Sally"* -> El agente responde saludando y guarda la conversación.
   - Mensaje 2: *"What's my name?"* -> El agente recupera el historial acumulado del hilo y responde *"Your name is Sally"*.

---

## 🚀 Cómo Ejecutar

Desde la raíz de `Building_Releable_Agents`:

```bash
python module-1/lesson-2/thread_agent.py
```
