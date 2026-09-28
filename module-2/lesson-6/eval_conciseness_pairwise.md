# Módulo 2 - Lección 6: `eval_conciseness_pairwise.py` (Juez Pareado de Concisión)

## 🎯 Propósito y Concepto Teórico

Este archivo define la lógica del **Juez Pareado (A/B)** utilizando un LLM (`qwen2.5:7b` en Ollama o `gpt-5-nano` en OpenAI) junto con el módulo [`token_utils.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/token_utils.py) para dictaminar cuál de dos respuestas (`Response A` o `Response B`) es más concisa, directa y eficiente sin omitir información crucial.

---

## ⚖️ Prevención de Sesgos en Evaluación Pareada

Al evaluar dos respuestas con un LLM, existen dos sesgos clásicos que distorsionan los resultados:

1. **Position Bias (Sesgo de Posición)**: Los LLMs tienden a preferir la Respuesta A sobre la B simplemente por aparecer primero en el prompt.
   * *Solución*: LangSmith incluye el parámetro `randomize_order=True` en `evaluate((exp_a, exp_b))` para barajar aleatoriamente el orden de presentación a nivel de cada ejemplo.
1. **Verbosity Bias (Sesgo de Verbosidad)**: Los LLMs tienden a asociar mayor longitud con mayor cortesía o completitud.
   * *Solución*: El prompt instruye explícitamente al juez a penalizar las frases de relleno ("Me complace informarle...") y premiar las respuestas directas. Además, se combinan las métricas cuantitativas de tokens de `token_utils.py`.

---

## 🧮 Integración con el Tokenizador

El evaluador pareado integra la comparación exacta de tokens (`tiktoken` con codificación `cl100k_base`):

* `calculate_conciseness_metrics(resp_a, resp_b)` calcula la reducción porcentual de tokens.
* Esto permite correlacionar el dictamen del LLM juez con el ahorro medible de tokens y latencia entre `agent_v4` y `agent_v5`.

---

## 🚀 Integración y Ejecución

1. **Modo Diagnóstico Local (sin costo de API, prueba directa con Ollama)**:

   ```bash
   uv run python module-2/lesson-6/eval_conciseness_pairwise.py
   ```

1. **Comparación Pareada de Experimentos en LangSmith**:

   ```bash
   uv run python module-2/lesson-6/eval_conciseness_pairwise.py <nombre-experimento-a> <nombre-experimento-b>
   ```

1. **Pipeline Todo-en-Uno (Ejecuta v4, v5 y la comparación pareada)**:

   ```bash
   uv run python module-2/lesson-6/run_pairwise_experiment.py
   ```

> Para el desglose pedagógico y teórico completo, consulta la [Guía Maestra de la Lección 6](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-6/LESSON_6_COMPLETE_GUIDE.md).
