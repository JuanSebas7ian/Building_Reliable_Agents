"""
token_utils.py - Utilidad central de Tokenización y Métricas para el Módulo 2

Proporciona conteo preciso de tokens usando `tiktoken` (con fallback automático),
extracción de métricas de tokens desde trazas de LangSmith y cálculo de concisión.
Diseñado para funcionar tanto con modelos OpenAI en la nube como con Ollama local (ej. qwen2.5:7b).
"""
import os
import re
from typing import Dict, Any, Optional

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    tiktoken = None  # type: ignore[assignment]


def get_encoder(model_name: Optional[str] = None):
    """
    Obtiene el codificador BPE de tiktoken adecuado.
    Si el modelo es de Ollama (ej. qwen2.5) o no se reconoce, usa 'cl100k_base' como estándar industrial.
    """
    if not _TIKTOKEN_AVAILABLE or tiktoken is None:
        return None

    model = model_name or os.getenv("CHAT_MODEL", "qwen2.5:7b").lower()

    # Mapeo a codificadores estándar
    try:
        if "gpt-4o" in model or "gpt-5" in model:
            return tiktoken.get_encoding("o200k_base")
        elif "gpt-4" in model or "gpt-3.5" in model:
            return tiktoken.encoding_for_model(model)
        else:
            # Para Qwen, Llama u otros modelos locales vía Ollama, cl100k_base aproxima muy bien el BPE
            return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model_name: Optional[str] = None) -> int:
    """
    Cuenta el número de tokens en una cadena de texto.
    Si tiktoken no está disponible o falla, utiliza una estimación heurística robusta (~4 caracteres por token).
    """
    if not text:
        return 0

    encoder = get_encoder(model_name)
    if encoder is not None:
        try:
            return len(encoder.encode(text))
        except Exception:
            pass

    # Heurística de fallback: promedio ~4 caracteres en inglés/español o conteo de palabras * 1.33
    words = len(re.findall(r"\w+|[^\w\s]", text, re.UNICODE))
    return max(1, int(words * 1.3))


def extract_tokens_from_run(run: Any) -> Dict[str, int]:
    """
    Extrae tokens de entrada, salida y total desde un objeto de ejecución de LangSmith (Run)
    o desde una respuesta de diccionario de OpenAI/Ollama.
    """
    metrics = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    run_inputs: Any = getattr(run, "inputs", None)
    if run_inputs is None and isinstance(run, dict):
        run_inputs = run.get("inputs")

    run_outputs: Any = getattr(run, "outputs", None)
    if run_outputs is None and isinstance(run, dict):
        run_outputs = run.get("outputs")

    # Si el objeto Run tiene métricas de uso de tokens
    if isinstance(run_outputs, dict):
        usage = run_outputs.get("usage", {}) or run_outputs.get("token_usage", {})
        if isinstance(usage, dict) and usage:
            metrics["prompt_tokens"] = usage.get("prompt_tokens", 0)
            metrics["completion_tokens"] = usage.get("completion_tokens", 0)
            metrics["total_tokens"] = usage.get("total_tokens", 0)

    # Si el objeto Run tiene inputs y outputs de texto directo y usage no viene en metadata
    if metrics["total_tokens"] == 0:
        in_text = ""
        out_text = ""
        if isinstance(run_inputs, dict):
            in_text = str(run_inputs.get("question", "") or run_inputs.get("input", ""))

        if isinstance(run_outputs, dict):
            out_text = str(run_outputs.get("output", "") or run_outputs.get("response", "") or run_outputs.get("answer", ""))

        p_tokens = count_tokens(in_text) if in_text else 0
        c_tokens = count_tokens(out_text) if out_text else 0
        metrics["prompt_tokens"] = p_tokens
        metrics["completion_tokens"] = c_tokens
        metrics["total_tokens"] = p_tokens + c_tokens

    return metrics


def calculate_conciseness_metrics(response_a: str, response_b: str) -> Dict[str, Any]:
    """
    Compara dos respuestas (ej. Agent v4 vs Agent v5) en términos de longitud, palabras y tokens.
    Retorna métricas cuantitativas de concisión.
    """
    tokens_a = count_tokens(response_a)
    tokens_b = count_tokens(response_b)
    words_a = len(response_a.split())
    words_b = len(response_b.split())

    token_diff = tokens_a - tokens_b
    pct_reduction = (token_diff / tokens_a * 100) if tokens_a > 0 else 0.0

    return {
        "tokens_a": tokens_a,
        "tokens_b": tokens_b,
        "words_a": words_a,
        "words_b": words_b,
        "tokens_saved": token_diff,
        "percent_reduction": round(pct_reduction, 2),
        "is_b_more_concise": tokens_b < tokens_a,
    }


if __name__ == "__main__":
    # Test diagnóstico rápido
    test_text_a = (
        "Hello! Thank you so much for reaching out to OfficeFlow Supply Co. today. "
        "Regarding your question about copy paper, I would be absolutely delighted to inform you "
        "that we have standard letter-sized copy paper available in stock right now, and you can purchase it!"
    )
    test_text_b = "Yes, we have letter-sized copy paper in stock and ready to order."

    print("=== TEST DIAGNÓSTICO DE TOKENIZADOR ===")
    print(f"Tiktoken disponible: {_TIKTOKEN_AVAILABLE}")
    print(f"Tokens Respuesta A (Larga):  {count_tokens(test_text_a)}")
    print(f"Tokens Respuesta B (Corta):  {count_tokens(test_text_b)}")

    metrics = calculate_conciseness_metrics(test_text_a, test_text_b)
    print(f"Ahorro de tokens en B: {metrics['tokens_saved']} ({metrics['percent_reduction']}%)")
