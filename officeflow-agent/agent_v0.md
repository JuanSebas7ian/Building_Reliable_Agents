# Agente OfficeFlow: `agent_v0.py` (Línea Base)

## 🎯 Propósito y Contexto
`agent_v0.py` representa el **punto de partida (baseline)** en el ciclo de desarrollo del agente Emma. Es una implementación estándar utilizando directamente el SDK asíncrono de OpenAI (`AsyncOpenAI`) con function calling (OpenAI Tools) y memoria conversacional en memoria (`dict`).

---

## 🏗️ Arquitectura y Componentes

1. **Cliente de IA**:
   - `client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))`
   - No cuenta con ninguna capa de telemetría ni observabilidad configurada.

2. **Herramientas Disponibles**:
   - `query_database`: Ejecuta consultas SQL directamente sobre `inventory.db` mediante `sqlite3`.
   - `search_knowledge_base`: Realiza búsqueda semántica RAG sobre fragmentos (chunks) de texto de 200 caracteres con solapamiento de 20 caracteres mediante similitud coseno con embeddings de `text-embedding-3-small`.

3. **Prompt del Sistema (`system_prompt`)**:
   - Define la personalidad de Emma (especialista de Customer Experience en OfficeFlow).
   - Especifica qué puede atender (información de productos, stock, recomendaciones) y qué no puede gestionar directamente (pedidos, devoluciones, cambios de cuenta).
   - Instruye revisar la base de datos primero antes de hacer preguntas aclaratorias.

---

## ⚠️ Limitaciones y Fallos Detectados en v0

1. **Caja Negra (Sin Observabilidad)**:
   - Si el agente da una respuesta incorrecta o tarda demasiado, no hay visibilidad de qué SQL ejecutó, cuántas llamadas a la API realizó, o qué fragmentos del RAG recuperó.
2. **Adivinanza del Esquema de Base de Datos**:
   - El agente asume o adivina los nombres de las columnas y tablas en `inventory.db`. Si la consulta falla, reintenta a ciegas.
3. **Violación de Privacidad de Inventario**:
   - Responde con el número exacto de existencias (por ejemplo: "Tenemos exactamente 142 unidades de papel bond"), violando las políticas de negocio de la empresa.
4. **Pérdida de Contexto en RAG por Fragmentación Excesiva**:
   - La técnica de chunks de 200 caracteres rompe párrafos de políticas (por ejemplo, excepciones a devoluciones o costos de envío diferenciados).
5. **Verbosity (Exceso de Texto)**:
   - Respuestas excesivamente largas y reiterativas con preguntas de relleno al final.

---

## 🚀 Cómo Ejecutar

```bash
cd officeflow-agent
python agent_v0.py
```

Escribe preguntas en la consola como:
- *"¿Tienen papel de copia?"*
- *"¿Cuál es la política de devoluciones?"*
- *"Escribe 'quit' o 'exit' para salir."*
