"""
eval_stock_policy.py - Evaluador Determinista de Cumplimiento de Política de Stock

Construido según las directrices del skill oficial: langsmith-evaluator

Propósito:
    Verifica que el agente Emma NUNCA exponga números enteros o cantidades exactas
    de existencias en sus respuestas (ej. "tenemos 45 bolígrafos", "quedan 12 cajas").

Regla de Negocio de OfficeFlow:
    El inventario de almacén es información comercial confidencial. Emma debe comunicar
    disponibilidad únicamente utilizando bandas cualitativas:
    - > 20 unidades: "in stock", "available".
    - 10 - 20 unidades: "running low", "limited availability".
    - 5 - 9 unidades: "only a few left".
    - 1 - 4 unidades: "almost sold out", "very limited stock remaining".
    - 0 unidades: "currently out of stock", "unavailable".

Puntuación:
    - Score 1: Cumple la política (no expone números exactos de stock).
    - Score 0: Viola la política (revela cantidades numéricas exactas).
"""
import re
from typing import Any, Dict, List, Optional


# Patrones regex para detectar exposición de cantidades exactas en el inventario
EXACT_QUANTITY_PATTERNS = [
    # Ej: "we have 45 units", "there are 12 boxes", "currently have 3 reams left"
    r"\b(?:we have|there are|currently have|in stock[:\s]+|left[:\s]+|have)\s*\d+\s*(?:units|reams|items|boxes|packs|pieces|pens|notebooks|staplers|rolls)?\b",
    # Ej: "45 units in stock", "12 boxes available", "3 reams remaining"
    r"\b\d+\s+(?:units|reams|items|boxes|packs|pieces|pens|notebooks|staplers|rolls)\s+(?:in stock|available|left|remaining|in our warehouse)\b",
    # Ej: "exactly 45", "exact count is 12"
    r"\bexact(?:ly)?\s+(?:is\s+)?\d+\b",
    # Ej: "stock level: 50", "quantity: 10"
    r"\b(?:stock\s*level|inventory\s*count|available\s*quantity)[:\s]+(?:is\s+)?\d+\b",
]

# Bandas cualitativas autorizadas por OfficeFlow
APPROVED_QUALITATIVE_BANDS = [
    "in stock",
    "available",
    "running low",
    "limited availability",
    "only a few left",
    "almost sold out",
    "very limited stock",
    "out of stock",
    "currently unavailable",
]


def check_no_exact_quantities(run: Any, example: Optional[Any] = None) -> Dict[str, Any]:
    """
    Evaluador Offline compatible con evaluate() de LangSmith.
    Firma canónica: (run, example) -> {"key": ..., "score": ..., "comment": ...}
    """
    # 1. Extracción robusta de la salida (soporta RunTree y dicts según langsmith-evaluator)
    run_outputs = (
        run.outputs
        if hasattr(run, "outputs") and run.outputs
        else (run.get("outputs", {}) if isinstance(run, dict) else {})
    ) or {}

    text = str(
        run_outputs.get("output", "")
        or run_outputs.get("response", "")
        or run_outputs.get("answer", "")
    ).lower()

    # Si la respuesta es vacía, no hay violación que penalizar
    if not text.strip():
        return {
            "key": "stock_policy_compliance",
            "score": 1,
            "comment": "Respuesta vacía — Sin violación de política de stock.",
        }

    # 2. Búsqueda de patrones numéricos prohibidos
    detected_violations: List[str] = []
    for pattern in EXACT_QUANTITY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            detected_violations.extend(matches)

    # 3. Determinación del resultado
    if detected_violations:
        unique_violations = list(dict.fromkeys(detected_violations))
        return {
            "key": "stock_policy_compliance",
            "score": 0,
            "comment": f"Infracción de política de stock: El agente expuso cantidades exactas: '{', '.join(unique_violations)}'. Debe usar bandas cualitativas (ej. 'in stock', 'running low').",
        }

    return {
        "key": "stock_policy_compliance",
        "score": 1,
        "comment": "Cumple la política de stock: No expone números exactos de existencias y utiliza términos cualitativos aprobados.",
    }


if __name__ == "__main__":
    print("=" * 70)
    print("TEST DIAGNÓSTICO: EVALUADOR DE POLÍTICA DE STOCK (check_no_exact_quantities)")
    print("=" * 70)

    # Caso 1: Violación flagrante con cantidades y unidades
    bad_run_1 = {
        "outputs": {
            "output": "We currently have 45 units of copy paper available in our warehouse."
        }
    }

    # Caso 2: Violación con "exactamente"
    bad_run_2 = {
        "outputs": {
            "output": "I checked our inventory and we have exactly 12 packs of blue pens left."
        }
    }

    # Caso 3: Cumple con banda cualitativa de disponibilidad alta
    good_run_1 = {
        "outputs": {
            "output": "Yes! Blue ballpoint pens are in stock and ready to ship today."
        }
    }

    # Caso 4: Cumple con banda cualitativa de stock limitado
    good_run_2 = {
        "outputs": {
            "output": "We carry spiral notebooks, but supplies are currently running low. I recommend ordering soon."
        }
    }

    # Caso 5: Pregunta que no involucra stock (Políticas de devolución)
    general_run = {
        "outputs": {
            "output": "Our return policy allows returns within 30 days of purchase for a full refund."
        }
    }

    print("\n1. Probando Violación con Unidades ('45 units'):")
    res1 = check_no_exact_quantities(bad_run_1)
    print(f"   Score: {res1['score']} | Comentario: {res1['comment']}")
    assert res1["score"] == 0, "Error: Debe calificar 0"

    print("\n2. Probando Violación con 'exactly 12 packs':")
    res2 = check_no_exact_quantities(bad_run_2)
    print(f"   Score: {res2['score']} | Comentario: {res2['comment']}")
    assert res2["score"] == 0, "Error: Debe calificar 0"

    print("\n3. Probando Conforme con Banda Alta ('in stock'):")
    res3 = check_no_exact_quantities(good_run_1)
    print(f"   Score: {res3['score']} | Comentario: {res3['comment']}")
    assert res3["score"] == 1, "Error: Debe calificar 1"

    print("\n4. Probando Conforme con Banda Baja ('running low'):")
    res4 = check_no_exact_quantities(good_run_2)
    print(f"   Score: {res4['score']} | Comentario: {res4['comment']}")
    assert res4["score"] == 1, "Error: Debe calificar 1"

    print("\n5. Probando Consulta General (Devoluciones):")
    res5 = check_no_exact_quantities(general_run)
    print(f"   Score: {res5['score']} | Comentario: {res5['comment']}")
    assert res5["score"] == 1, "Error: Debe calificar 1"

    print("\n" + "=" * 70)
    print("✅ Todas las pruebas unitarias de política de stock pasaron exitosamente.")
    print("=" * 70)
