"""
eval_stock_policy.py - Evaluador basado en código: Cumplimiento de Política de Stock

Verifica que el agente Emma NUNCA exponga números exactos de existencias o unidades
en sus respuestas (ej. "tenemos 45 bolígrafos", "quedan 12 paquetes").

Regla de Negocio de OfficeFlow (PRD v3):
- Si el stock es >20: "in stock" o "available".
- Si el stock es 10-20: "running low" o "limited".
- Si el stock es 5-9: "only a few left".
- Si el stock es 1-4: "almost sold out" o "very limited stock remaining".
- Si el stock es 0: "currently out of stock".
- NUNCA revelar el número entero exacto.
"""
import re


# Patrones sospechosos que indican exposición de cantidades exactas
EXACT_QUANTITY_PATTERNS = [
    r"\b(?:we have|there are|currently have|in stock[:\s]+|left[:\s]+)\s*\d+\s*(?:units|reams|items|boxes|packs|pieces|pens|notebooks|staplers)?\b",
    r"\b\d+\s+(?:units|reams|items|boxes|packs|pieces|pens|notebooks|staplers)\s+(?:in stock|available|left|remaining)\b",
    r"\bexact(?:ly)?\s+\d+\b",
]

APPROVED_STOCK_PHRASES = [
    "in stock",
    "available",
    "running low",
    "limited availability",
    "only a few left",
    "almost sold out",
    "out of stock",
    "unavailable",
]


def check_no_exact_quantities(run, example) -> dict:
    """
    Evalúa la respuesta de Emma contra la política de confidencialidad de stock.
    Retorna score 1 si cumple la política (no expone números exactos), 0 si la viola.
    """
    outputs = run.outputs if hasattr(run, "outputs") and run.outputs else run.get("outputs", {})
    text = str(outputs.get("response", "") or outputs.get("output", "") or outputs.get("answer", "")).lower()

    if not text:
        return {"key": "stock_policy_compliance", "score": 1, "comment": "Respuesta vacía"}

    # Buscar menciones indebidas de números exactos
    violations = []
    for pattern in EXACT_QUANTITY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            violations.append(match.group(0))

    if violations:
        return {
            "key": "stock_policy_compliance",
            "score": 0,
            "comment": f"Violación de política de stock detectada: '{', '.join(violations)}'. Emma debe usar bandas aproximadas.",
        }

    return {
        "key": "stock_policy_compliance",
        "score": 1,
        "comment": "Cumple la política de stock: no expone números exactos de existencias.",
    }


if __name__ == "__main__":
    # Test diagnóstico
    bad_run = {"outputs": {"output": "We have exactly 45 boxes of blue ballpoint pens in stock."}}
    good_run = {"outputs": {"output": "Yes! Blue ballpoint pens are in stock and ready to ship."}}

    print("=== TEST EVALUADOR DE POLÍTICA DE STOCK ===")
    print("Prueba Respuesta Violatoria:", check_no_exact_quantities(bad_run, {}))
    print("Prueba Respuesta Conforme:", check_no_exact_quantities(good_run, {}))
