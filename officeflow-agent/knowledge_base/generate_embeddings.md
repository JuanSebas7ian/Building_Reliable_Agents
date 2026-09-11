# Utilidad de Embeddings: `generate_embeddings.py`

## 🎯 Propósito
Este script es la utilidad encargada de precalcular los vectores de embedding para todos los documentos de políticas de la base de conocimiento (`knowledge_base/documents/*.md`) utilizando el modelo de embeddings de OpenAI `text-embedding-3-small` y persistirlos en `knowledge_base/embeddings/embeddings.json`.

---

## ⚙️ Funcionamiento Interno

1. **Lectura de Documentos**:
   - Escanea todos los archivos Markdown en `documents/`:
     - `company_info.md`: Reseña de OfficeFlow Supply Co.
     - `locations_contact.md`: Directorio de centros de distribución y oficinas.
     - `ordering_policy.md`: Términos de pedidos, compras mayoristas y pagos.
     - `returns_policy.md`: Política de devoluciones y garantías.
     - `shipping_policy.md`: Tiempos de entrega y zonas de cobertura.

2. **Generación con OpenAI**:
   - Envía el contenido íntegro de cada documento al endpoint de embeddings:
     ```python
     response = client.embeddings.create(
         model="text-embedding-3-small",
         input=content
     )
     ```

3. **Serialización a JSON**:
   - Guarda una estructura estructurada:
     ```json
     {
       "docs": [["company_info.md", "...texto..."], ...],
       "embeddings": [[0.012, -0.043, ...], ...]
     }
     ```

---

## 🚀 Cómo Ejecutar

Si modificas o agregas algún documento de políticas en `knowledge_base/documents/`:

```bash
cd officeflow-agent/knowledge_base
python generate_embeddings.py
```
*(Nota: Requiere tener configurada la variable `OPENAI_API_KEY` en el archivo `.env`).*
