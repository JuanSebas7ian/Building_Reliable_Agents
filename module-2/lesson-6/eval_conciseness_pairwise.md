# Módulo 2 - Lección 6: `eval_conciseness_pairwise.py` (Juez Pareado de Concisión)

## 🎯 Propósito y Concepto Teórico
Este archivo define la lógica del **Juez Pareado** utilizando un LLM (`gpt-5-nano` o equivalente) con un schema estructurado para dictaminar cuál de dos respuestas (`Response A` o `Response B`) es más concisa, directa y útil para el usuario final.

---

## ⚖️ Prevención de Sesgos en Evaluación Pareada

Al evaluar dos respuestas con un LLM, existen sesgos conocidos:
1. **Position Bias (Sesgo de Posición)**: Los LLMs tienden a preferir la Respuesta A por sobre la B simplemente por aparecer primero en el prompt.
   - *Solución*: LangSmith incluye el parámetro `randomize_order=True` en `evaluate((exp_a, exp_b))` para barajar aleatoriamente el orden de las respuestas y neutralizar este sesgo.
2. **Verbosity Bias (Sesgo de Verbosidad)**: Los LLMs suelen asumir erróneamente que las respuestas más largas son más completas o educadas.
   - *Solución*: El prompt de evaluación en este script instruye enfáticamente al juez a penalizar las palabras de relleno y premiar las respuestas directas.

---

## 🔍 Schema de Salida Estructurada

El juez responde forzando un formato JSON estructurado:
```python
class ConcisenessChoice(BaseModel):
    reasoning: str  # Explicación paso a paso de la decisión
    preferred: Literal["A", "B", "TIE"]  # Ganador o empate
```

---

## 🚀 Integración

Esta función se pasa como evaluador en `run_pairwise_experiment.py`:
```python
from eval_conciseness_pairwise import conciseness_evaluator
```
