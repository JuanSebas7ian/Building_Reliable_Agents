# Agente OfficeFlow: `agent_v5.py` (+ Optimización de Concisión)

## 🎯 Propósito y Contexto
Aunque `agent_v4.py` alcanzó alta precisión fáctica y respetó las políticas del PRD, las pruebas con usuarios y la inspección de trazas en LangSmith revelaron un problema de experiencia de usuario y eficiencia operativa: **el agente era demasiado verboso y prolijo**.

Emma generaba respuestas extensas con múltiples párrafos de cortesía y preguntas innecesarias al final. Esto generaba:
- Mayor latencia (Time To First Token y tiempo total de generación).
- Mayor consumo y coste de tokens de salida (`completion tokens`).
- Fricción para los clientes que solo querían una respuesta rápida y directa.

`agent_v5.py` implementa directrices estrictas de **concisión y brevedad**, además de actualizar los ejemplos de interacción (*few-shot examples*) en el prompt del sistema.

---

## 🔄 Cambios Respecto a `agent_v4.py`

### 1. Inclusión de la Directriz `CONCISENESS PRIORITY` en el System Prompt
```markdown
CONCISENESS PRIORITY:
Your responses should be brief and to the point. Avoid unnecessary filler, repetition, or overly elaborate explanations. Get straight to the answer. If you can say something in one sentence, don't use three. Customers appreciate quick, direct answers over lengthy responses.
```

### 2. Ejemplos de Interacción Refactorizados a Versión Concisa

- **Ejemplo 1 (Papel de copia)**:
  - *Antes (v4)*: "Yes, we do! We carry several types of copy paper. Are you looking for standard 8.5x11 inch letter size, or do you need a specific weight or finish? I can check what we have in stock."
  - *Ahora (v5)*: "Yes! We carry several types. Are you looking for standard 8.5x11, or a specific weight or finish?"

- **Ejemplo 2 (Devoluciones)**:
  - *Antes (v4)*: "I understand you need to process a return. While I can't handle returns directly, our Returns Department will be happy to help you. You can reach them at returns@officeflow.com or call 1-800-OFFICE-1 ext. 3. They typically respond within 4 business hours. Do you need any other information I can help with?"
  - *Ahora (v5)*: "Our Returns Department handles that - reach them at returns@officeflow.com or 1-800-OFFICE-1 ext. 3. They respond within 4 business hours. Anything else I can help with?"

- **Ejemplo 3 (Bolígrafo para firmas)**:
  - *Antes (v4)*: "For document signing, I'd recommend a pen with archival-quality ink that won't fade over time. Let me check what we have available that would work well for that purpose."
  - *Ahora (v5)*: "For document signing, I'd recommend a pen with archival-quality ink. Let me check what we have available."

---

## ⚖️ Evaluación Pareada A/B (`v4` vs `v5`)
En el Módulo 2 (Lección 6), este cambio se valida científicamente utilizando **Pairwise Evaluation** (`run_pairwise_experiment.py`):
Un LLM juez recibe a ciegas la respuesta de `v4` y la de `v5` para las 25 preguntas del dataset corporativo y vota cuál respuesta es superior en concisión y utilidad directa.

---

## 🚀 Cómo Ejecutar

```bash
cd officeflow-agent
python agent_v5.py
```
