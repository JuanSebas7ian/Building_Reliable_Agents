"""
eval_schema_check.py - Evaluador Determinista de Trayectoria SQL

Construido según las directrices del skill oficial: langsmith-evaluator

Propósito:
    Inspecciona la secuencia de 'tool_calls' en el historial de mensajes de Emma
    para verificar que, si utiliza la herramienta 'query_database', SIEMPRE realice
    una inspección previa del esquema (mediante PRAGMA table_info o sqlite_master)
    ANTES de lanzar la primera consulta de datos (SELECT).

Puntuación:
    - Score 1: Si inspeccionó el esquema antes del primer SELECT, o si la pregunta
               no requería interactuar con la base de datos (No aplicable).
    - Score 0: Si intentó adivinar tablas o columnas lanzando un SELECT directo
               sin consultar previamente los metadatos de la base de datos.
"""
import json
import re
from typing import Any, Dict, List


# Patrones SQL que denotan inspección de metadatos o estructura de la base de datos
SCHEMA_PATTERNS = [
    r"PRAGMA\s+table_info",
    r"SELECT\s+.*FROM\s+sqlite_master",
    r"PRAGMA\s+database_list",
    r"\.schema",
]


def _is_schema_query(sql_text: str) -> bool:
    """Retorna True si la cadena contiene una instrucción de inspección de esquema."""
    for pattern in SCHEMA_PATTERNS:
        if re.search(pattern, sql_text, re.IGNORECASE):
            return True
    return False


def _extract_sql_from_arguments(raw_args: Any) -> str:
    """Extrae el texto SQL del argumento, soportando strings planos o JSON dicts."""
    if isinstance(raw_args, dict):
        return str(raw_args.get("query") or raw_args.get("sql") or json.dumps(raw_args))
    if isinstance(raw_args, str):
        try:
            parsed = json.loads(raw_args)
            if isinstance(parsed, dict):
                return str(parsed.get("query") or parsed.get("sql") or raw_args)
        except Exception:
            pass
        return raw_args
    return str(raw_args)


def _extract_tool_calls(run: Any) -> List[Dict[str, str]]:
    """
    Extrae las llamadas a herramientas desde los outputs del Run.
    Cumple con el estándar de langsmith-evaluator para soportar RunTree o dicts.
    """
    run_outputs = run.outputs if hasattr(run, "outputs") and run.outputs else (run.get("outputs", {}) if isinstance(run, dict) else {}) or {}
    messages = run_outputs.get("messages", [])

    tool_calls = []
    for msg in messages:
        if isinstance(msg, dict):
            # Mensajes tipo dict estándar
            for tc in msg.get("tool_calls", []):
                func = tc.get("function", {})
                tool_calls.append({
                    "name": func.get("name", ""),
                    "arguments": _extract_sql_from_arguments(func.get("arguments", "")),
                })
        elif hasattr(msg, "tool_calls") and msg.tool_calls:
            # Objetos de mensaje tipo LangChain BaseMessage
            for tc in msg.tool_calls:
                tool_calls.append({
                    "name": getattr(tc, "name", "") or (tc.get("name") if isinstance(tc, dict) else ""),
                    "arguments": _extract_sql_from_arguments(getattr(tc, "args", "") or (tc.get("args") if isinstance(tc, dict) else "")),
                })
    return tool_calls


def schema_before_query(run: Any, example: Any = None) -> Dict[str, Any]:
    """
    Evaluador Offline compatible con evaluate() de LangSmith.
    Firma: (run, example) -> {"key": ..., "score": ..., "comment": ...}
    """
    tool_calls = _extract_tool_calls(run)

    # Filtrar únicamente las llamadas dirigidas a la base de datos
    db_calls = [tc for tc in tool_calls if tc["name"] == "query_database"]

    # Caso 1: La consulta no requería SQL (ej. preguntas sobre políticas de envío o devoluciones)
    if not db_calls:
        return {
            "key": "schema_before_query",
            "score": 1,
            "comment": "No se realizaron llamadas a query_database — Verificación de esquema no aplicable.",
        }

    # Caso 2: Auditar la secuencia cronológica de consultas
    seen_schema_check = False
    for idx, tc in enumerate(db_calls):
        sql = tc.get("arguments", "")
        if _is_schema_query(sql):
            seen_schema_check = True
        else:
            # Se detectó una consulta de datos (SELECT)
            if not seen_schema_check:
                return {
                    "key": "schema_before_query",
                    "score": 0,
                    "comment": f"Infracción: El agente ejecutó una consulta de datos sin verificar el esquema primero. Query #{idx + 1}: '{sql[:120]}...'",
                }
            # Si ya se había inspeccionado el esquema previamente, la prueba se supera con éxito
            break

    if seen_schema_check:
        return {
            "key": "schema_before_query",
            "score": 1,
            "comment": "Cumple la trayectoria: El agente inspeccionó el esquema de la BD antes de consultar datos.",
        }

    return {
        "key": "schema_before_query",
        "score": 1,
        "comment": "Todas las consultas a la base de datos fueron inspecciones de esquema válidas.",
    }


if __name__ == "__main__":
    print("=" * 70)
    print("TEST DIAGNÓSTICO: EVALUADOR DE TRAYECTORIA SQL (schema_before_query)")
    print("=" * 70)

    # Caso de prueba A: Agente disciplinado (Primero PRAGMA, luego SELECT)
    good_run = {
        "outputs": {
            "messages": [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"function": {"name": "query_database", "arguments": '{"query": "PRAGMA table_info(items);"}'}}
                    ]
                },
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"function": {"name": "query_database", "arguments": '{"query": "SELECT sku_label FROM items WHERE sku_label LIKE \'%paper%\';"}'}}
                    ]
                }
            ]
        }
    }

    # Caso de prueba B: Agente indisciplinado (Lanza SELECT a ciegas sin revisar esquema)
    bad_run = {
        "outputs": {
            "messages": [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"function": {"name": "query_database", "arguments": '{"query": "SELECT * FROM products WHERE name = \'pens\';"}'}}
                    ]
                }
            ]
        }
    }

    # Caso de prueba C: Pregunta que no usa base de datos (RAG de políticas)
    no_sql_run = {
        "outputs": {
            "messages": [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"function": {"name": "search_knowledge_base", "arguments": '{"query": "return policy"}'}}
                    ]
                }
            ]
        }
    }

    print("\n1. Probando Agente Disciplinado (PRAGMA -> SELECT):")
    res_good = schema_before_query(good_run)
    print(f"   Score: {res_good['score']} | Comentario: {res_good['comment']}")
    assert res_good["score"] == 1, "Error: Debe calificar 1"

    print("\n2. Probando Agente Indisciplinado (SELECT directo a ciegas):")
    res_bad = schema_before_query(bad_run)
    print(f"   Score: {res_bad['score']} | Comentario: {res_bad['comment']}")
    assert res_bad["score"] == 0, "Error: Debe calificar 0"

    print("\n3. Probando Agente sin SQL (Solo RAG):")
    res_nosql = schema_before_query(no_sql_run)
    print(f"   Score: {res_nosql['score']} | Comentario: {res_nosql['comment']}")
    assert res_nosql["score"] == 1, "Error: Debe calificar 1 (No aplicable)"

    print("\n" + "=" * 70)
    print("✅ Todas las pruebas unitarias del evaluador pasaron exitosamente.")
    print("=" * 70)
