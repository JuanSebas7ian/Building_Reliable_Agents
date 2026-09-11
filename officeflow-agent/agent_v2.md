# Agente OfficeFlow: `agent_v2.py` (+ Instrucciones de Esquema SQL)

## 🎯 Propósito y Contexto
En `agent_v1.py`, al inspeccionar las trazas en LangSmith durante preguntas como *"¿Tienen bolígrafos azules y cuántos quedan?"*, se observó un patrón de error recurrente: **el agente generaba sentencias SQL adivinando los nombres de las columnas** (por ejemplo, `SELECT stock FROM products`, cuando la columna real era `quantity_in_stock`). Esto causaba errores de ejecución de SQLite y obligaba al agente a corregirse torpemente o a responder con información inventada (alucinación).

`agent_v2.py` soluciona esto introduciendo una estrategia de **descubrimiento previo del esquema en la definición de la herramienta**.

---

## 🔄 Cambios Respecto a `agent_v1.py`

### Actualización de la Definición de la Herramienta `QUERY_DATABASE_TOOL`

En lugar de una descripción genérica como *"SQL query to execute against the inventory database"*, se le proporcionan instrucciones explícitas de inspección obligatoria:

```python
QUERY_DATABASE_TOOL = {
    "type": "function",
    "function": {
        "name": "query_database",
        "description": "SQL query to get information about our inventory for customers like products, quantities and prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": """SQL query to execute against the inventory database.

YOU DO NOT KNOW THE SCHEMA. ALWAYS discover it first:
1. Query 'SELECT name FROM sqlite_master WHERE type="table"' to see available tables
2. Use 'PRAGMA table_info(table_name)' to inspect columns for each table
3. Only after understanding the schema, construct your search queries"""
                }
            },
            "required": ["query"]
        }
    }
}
```

---

## 📈 Impacto en el Comportamiento y en las Trazas

Al hacer una pregunta sobre el inventario en `agent_v2.py`:
1. **Paso 1**: El agente emite primero `SELECT name FROM sqlite_master WHERE type="table"`.
2. **Paso 2**: Revisa las columnas con `PRAGMA table_info('inventory')`.
3. **Paso 3**: Genera la consulta exacta con las columnas correctas (`SELECT product_name, quantity_in_stock, unit_price FROM ...`).

En el Módulo 2 (Lección 4), creamos un evaluador de código determinista (`eval_schema_check.py`) precisamente para validar automáticamente que el agente siempre ejecute este chequeo de esquema antes de consultar los datos.

---

## 🚀 Cómo Ejecutar

```bash
cd officeflow-agent
python agent_v2.py
```
