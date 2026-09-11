# Agente OfficeFlow: `agent_v4.py` (+ RAG sin Fragmentación / No-Chunking)

## 🎯 Propósito y Contexto
En `agent_v3.py`, las políticas de la empresa (envíos, devoluciones, condiciones de facturación) se recuperaban mediante un RAG tradicional con fragmentación de texto fija (`chunk_size=200, overlap=20`).

Al analizar las trazas de LangSmith para preguntas complejas como:
- *"¿Puedo devolver un producto después de 30 días si el paquete está abierto?"*
- *"¿El envío express aplica a Alaska y Hawái?"*

Se descubrió que el recuperador semántico devolvía fragmentos aislados que carecían de las cláusulas condicionales o excepciones que se encontraban en el párrafo anterior o posterior del documento Markdown original. El agente terminaba respondiendo incorrectamente.

`agent_v4.py` resuelve este problema eliminando el chunking por completo (**No-Chunking RAG**), indexando e inyectando **documentos completos** en el contexto.

---

## 🔄 Cambios Respecto a `agent_v3.py`

1. **Eliminación de la función `chunk_text`**:
   - Ya no se divide el texto en trozos pequeños de 200 caracteres.
2. **Indexación de Documentos Completos**:
   - Cada archivo Markdown de la base de conocimiento (`knowledge_base/documents/*.md`) se indexa como una unidad semántica íntegra:
   ```python
   # Se genera un embedding por cada documento completo:
   response = await client.embeddings.create(
       model="text-embedding-3-small",
       input=content
   )
   ```
3. **Caché Inteligente con Verificación de Modificación (`_embeddings_are_stale`)**:
   - Si se edita cualquier archivo `.md` dentro de `knowledge_base/documents/`, el agente detecta automáticamente que la fecha de modificación es más reciente que `embeddings.json` y regenera la caché.
4. **Respuesta RAG con Documento Entero**:
   - `search_knowledge_base` recupera los `top_k` documentos completos más similares, garantizando que el modelo cuente con todas las condiciones, excepciones y detalles legales del documento.

---

## 💡 Lección de Diseño de Agentes RAG
En bases de conocimiento corporativas compuestas por políticas cortas o medianas (1 a 5 páginas por documento), fragmentar el texto a menudo destruye el contexto sintáctico y normativo. Con los límites de contexto modernos de los LLMs (128k a 1M+ tokens), recuperar el documento completo suele ser más preciso, robusto y fácil de mantener.

---

## 🚀 Cómo Ejecutar

```bash
cd officeflow-agent
python agent_v4.py
```
