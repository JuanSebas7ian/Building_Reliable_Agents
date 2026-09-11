# Módulo 2 - Lección 4: `eval_schema_check.py` (Evaluador Basado en Código)

## 🎯 Propósito y Concepto Teórico
Los evaluadores deterministas basados en código (**Code-based Evaluators**) son el equivalente a los **tests unitarios** del desarrollo de software tradicional aplicados a agentes de IA. Son:
- **100% Deterministas**: No dependen de un modelo estocástico ni alucinan.
- **Rápidos y Gratuitos**: No consumen tokens ni incurren en latencia de llamadas a APIs externas.
- **Ideales para Validar Comportamientos Estructurales**: Verificación de formatos JSON/XML, detección de palabras clave prohibidas o, como en este caso, **inspección de las llamadas a herramientas (tool calls)**.

---

## 🔍 Lógica del Evaluador `schema_before_query`

Este evaluador audita que, siempre que el agente decida consultar la base de datos de inventario (`query_database`), haya inspeccionado primero el esquema de la base de datos antes de enviar cualquier consulta de datos.

### Expresiones Regulares de Inspección de Esquema
```python
SCHEMA_PATTERNS = [
    r"PRAGMA\s+table_info",
    r"SELECT\s+.*FROM\s+sqlite_master",
    r"PRAGMA\s+database_list",
    r"\.schema",
]
```

### Reglas de Puntuación:
1. **Puntuación = 1 (Pasa)**:
   - El agente no usó la base de datos (pregunta sobre políticas o general).
   - O bien, el agente ejecutó una consulta que coincide con `SCHEMA_PATTERNS` antes de su primera consulta con `SELECT ... FROM inventory`.
2. **Puntuación = 0 (Falla)**:
   - El agente ejecutó una consulta de datos directa sin haber inspeccionado previamente las tablas o columnas de SQLite.

---

## 🧩 Integración con LangSmith
La firma de la función:
```python
def schema_before_query(run, example) -> dict:
```
Recibe el objeto `run` completo (que contiene los mensajes, herramientas invocadas y argumentos) y el `example` del dataset. Devuelve un diccionario con:
- `score`: `1` (éxito) o `0` (fallo).
- `comment`: Explicación detallada de por qué pasó o falló la evaluación, visible en la UI de LangSmith.
