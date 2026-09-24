# Módulo 2 - Lección 5: `eval_llm_judge.py` (Evaluador LLM-as-a-Judge)

## 🎯 Propósito y Concepto Teórico

En la ingeniería de agentes confiables, los evaluadores de código puro (regex, assertions) son excelentes para reglas rígidas como sintaxis y restricciones numéricas. Sin embargo, fallan cuando se trata de medir dimensiones cualitativas y subjetivas:
- **Tono y Empatía**: ¿Fue la respuesta cálida, humana y respetuosa o fría y robótica?
- **Claridad y Utilidad (*Helpfulness*)**: ¿Resolvió el problema del usuario con precisión y sin rodeos?
- **Cumplimiento de Protocolo de Soporte**: Si la consulta excedía las capacidades del agente (devoluciones, facturación), ¿orientó al cliente con los correos oficiales y pasos a seguir?

Para estas dimensiones, la solución estándar de la industria es el patrón **LLM-as-a-Judge**: un modelo de lenguaje que actúa como evaluador independiente siguiendo una **rúbrica de evaluación rigurosa**.

---

## 🛠️ Arquitectura y Funcionamiento

### 1. Rúbrica Estructurada y Persona
El juez se instruye con un prompt especializado que define su rol como Auditor de Calidad (QA Evaluator) de OfficeFlow Supply Co. y establece criterios explícitos:

```python
JUDGE_PROMPT = """You are an expert QA evaluator for customer support interactions at OfficeFlow Supply Co.
Evaluate the assistant's response to the customer's question based on these criteria:
1. Helpfulness: Did it directly address the customer's request with accurate information?
2. Tone & Empathy: Was it warm, professional, and empathetic without robotic filler?
3. Policy Compliance: If unable to handle directly (returns, order tracking, technical issues), did it provide the correct department email or next steps?

Customer Question:
{question}

Assistant Response:
{response}

Respond in the following JSON format ONLY:
{{
    "score": <number between 1 and 5, where 5 is excellent and 1 is completely unhelpful or rude>,
    "passed": <true if score >= 3, false otherwise>,
    "reasoning": "<brief 1-2 sentence explanation of your score>"
}}"""
```

### 2. Formato de Salida y Normalización para LangSmith
LangSmith espera que los evaluadores devuelvan métricas numéricas comparables (usualmente normalizadas entre `0.0` y `1.0` o booleanas `0/1`), junto con una explicación textual:

* **Score Crudo**: Escala Likert de 1 a 5.
* **Score Normalizado**: $\text{score} = \frac{\text{raw\_score}}{5.0}$ (rango `0.2` a `1.0`).
* **Comment**: Justificación generada por el LLM juez para auditoría en el panel de LangSmith.

---

## 💻 Soporte Dual: Ollama Local y OpenAI Cloud

El script está optimizado para funcionar sin coste alguno utilizando tu GPU local con **Ollama** (`qwen2.5:7b`), o alternativamente con OpenAI (`gpt-4o-mini` / `gpt-5-nano`):

```python
BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
```

---

## 🚀 Cómo Probar de Forma Aislada

Para ejecutar el diagnóstico unitario sin ejecutar el agente completo ni el dataset:

```bash
uv run python module-2/lesson-5/eval_llm_judge.py
```
