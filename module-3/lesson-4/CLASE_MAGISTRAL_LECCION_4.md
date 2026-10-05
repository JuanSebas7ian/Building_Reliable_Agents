# Clase Magistral: Lección 4 — Automations y el Cierre del Data Flywheel

> **Módulo 3: Moving Towards Production**  
> **Tema:** Reglas de Automatización en Tiempo Real, Acciones Reactivas y el Ciclo Virtuoso de Mejora Continua (Data Flywheel).  
> **Código Asociado:** [`automations_pipeline.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-4/automations_pipeline.py)

---

## 1. El Reto: De la Observabilidad Pasiva a la Acción Automatizada

En las lecciones anteriores construimos los pilares de telemetría y evaluación:
1. **Lección 1:** Telemetría en producción, metadata y feedback del usuario.
2. **Lección 2:** Insights Agent para minería masiva y agrupamiento de fallos sistémicos.
3. **Lección 3:** Online Evals para calificar y detectar anomalías en streaming.

Sin embargo, si la detección de un fallo requiere que un ingeniero abra manualmente un dashboard cada mañana para inspeccionar trazas, **el sistema sigue siendo frágil y lento para evolucionar**.

Las **Automations (Automatizaciones)** en LangSmith transforman la observabilidad pasiva en un sistema reactivo y autónomo: permiten definir reglas que, ante eventos específicos en el flujo de trazas, ejecutan acciones inmediatas sin intervención humana.

---

## 2. El Ciclo Virtuoso: The Data Flywheel

El objetivo supremo de la ingeniería de agentes confiables es cerrar el **Data Flywheel** (el volante de inercia de datos). Los fallos reales que ocurren en producción deben convertirse automáticamente en el combustible que entrena y valida la siguiente versión del agente.

```mermaid
flowchart TD
    subgraph "Ambiente de Producción (Tráfico Real)"
        User([Usuario Real]) -->|1. Consulta| ProdAgent[Agente en Producción]
        ProdAgent -->|2. Respuesta| User
        User -.->|3. Feedback (👍 / 👎)| Telemetry[Telemetría & Tracing]
        ProdAgent -.->|4. Traza Completa| Telemetry
    end

    subgraph "Online Evals & Automations Engine"
        Telemetry --> OnlineEval[Online Evals en Streaming]
        OnlineEval -->|Scores & Flags| AutoEngine{Motor de Automatizaciones}
        
        AutoEngine -->|Condición Cumplida| Action1[🏷️ Auto-Tagging: 'needs_review']
        AutoEngine -->|Condición Cumplida| Action2[📢 Webhook: Alerta a Slack / PagerDuty]
        AutoEngine -->|Fallo Relevante| Action3[📥 Auto-Add to Dataset: 'production-regressions']
    end

    subgraph "Ambiente de Desarrollo & CI/CD (Offline)"
        Action3 --> GoldenDS[(Golden Dataset de Regresiones)]
        GoldenDS --> OfflineEval[Offline Evals en CI/CD (evaluate)]
        Dev([Equipo de IA / Prompt Engineers]) -->|5. Refactoriza Prompts / Tools| NextAgent[Agente vNext]
        NextAgent --> OfflineEval
        OfflineEval -->|Supera Baseline| Deploy[🚀 Despliegue a Producción]
    end

    Deploy --> ProdAgent
```

---

## 3. Anatomía de una Regla de Automatización

Toda automatización en LangSmith consta de dos componentes esenciales:
1. **Trigger (Disparador / Filtro):** La condición lógica bajo la cual se activa la regla.
2. **Action (Acción):** La operación que se ejecuta sobre la traza o el sistema externo.

### Triggers Comunes en Producción:
* **Fallo de Guardrail / Política:** `stock_policy_check.score == 0.0` o `department_routing_check.score == 0.0`.
* **Feedback Negativo Explícito:** `user_feedback.score == 0` (Thumbs Down).
* **Alucinación o Incoherencia:** `context_faithfulness.score == 0.0`.
* **Violación de SLA de Rendimiento:** `latency > 5000ms` o `total_tokens > 4000`.
* **Excepción de Software:** `has(outputs, "error")` o fallo en ejecución de tool.

### Acciones Principales:
* **Tagging Dinámico:** Agregar etiquetas como `policy_breach`, `hallucination_detected`, `investigate_latency`.
* **Alertas Externas:** Disparar webhooks hacia canales de Slack de guardia (`#alerts-agent-production`) o PagerDuty.
* **Curación de Datasets (Data Flywheel):** Insertar la entrada y salida de la traza directamente en un dataset (`production-regressions`).

---

## 4. Implementación en Código: `automations_pipeline.py`

En [`automations_pipeline.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-4/automations_pipeline.py), diseñamos una arquitectura modular y desacoplada:

### A. Definición de la Regla (`AutomationRule`)
```python
class AutomationRule:
    def __init__(self, name, condition_description, tags_to_add, send_webhook, add_to_dataset=None):
        self.name = name
        self.condition_description = condition_description
        self.tags_to_add = tags_to_add
        self.send_webhook = send_webhook
        self.add_to_dataset = add_to_dataset

    def evaluate(self, trace: Dict[str, Any]) -> bool:
        # Evaluación de condiciones lógicas sobre traza, feedback o latencia
        ...
```

### B. Ejecución de Acciones y Curación Automática
```python
def add_to_langsmith_dataset(self, dataset_name, question, response, failure_reason):
    # Si el cliente LangSmith está disponible, crea el ejemplo en la nube:
    if self.client:
        self.client.create_example(
            inputs={"question": question},
            outputs={"expected": "Respuesta corregida pendiente de revisión humana."},
            metadata={"failure_reason": failure_reason, "source": "automation_flywheel"},
            dataset_id=dataset.id
        )
```

---

## 5. Simulación Práctica: 4 Escenarios de Tráfico Real

Al ejecutar el pipeline con [`automations_pipeline.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-4/automations_pipeline.py):

1. **`run_prod_101_ok` (Consulta Limpia):**
   * *Pregunta:* "¿Cuál es el plazo de devolución para artículos de papelería defectuosos?"
   * *Resultado:* ✅ Cumple todas las reglas. No se dispara ninguna acción.

2. **`run_prod_102_leak` (Fuga de Inventario):**
   * *Pregunta:* "¿Cuántos bolígrafos ejecutivos tienen ahora mismo?"
   * *Respuesta:* Reveló 150 unidades exactas en pasillo 4.
   * *Acción Disparada:* Regla `Policy Violation Rule` -> Tags `policy_breach`, `needs_human_review` -> Alerta a Slack -> **Caso exportado a dataset `production-regressions`**.

3. **`run_prod_103_bad` (Alucinación + Thumbs Down):**
   * *Pregunta:* "¿Puedo devolver un paquete abierto de marcadores?"
   * *Respuesta:* Negó categóricamente cualquier devolución de paquetes abiertos (contrario a la política del PRD que sí lo permite para defectuosos).
   * *Acciones Disparadas:* Reglas `User Dislike Rule` y `Faithfulness Hallucination Rule` -> Tags `user_negative_feedback`, `hallucination_detected` -> Alerta a Slack -> **Caso exportado a dataset `production-regressions`**.

4. **`run_prod_104_slow` (Brecha de SLA de Latencia):**
   * *Latencia:* `7820 ms` (SLA: `< 5000 ms`).
   * *Acción Disparada:* Regla `High Latency SLA Rule` -> Tag `latency_sla_breach` -> Alerta a Slack. (No se añade al dataset de precisión semántica, solo de performance).

---

## 6. Configuración en la Plataforma LangSmith

En la interfaz gráfica de LangSmith:
1. Navega a **Project Settings -> Automations** (o pestaña **Rules**).
2. Haz clic en **Add Rule**.
3. **Filter:** Escribe la expresión en el editor de filtros:
   ```text
   eq(feedback_key("stock_policy_check"), 0) or eq(feedback_key("user_feedback"), 0)
   ```
4. **Sampling Rate:** `100%` (aplica a todas las trazas coincidentes).
5. **Action:**
   * Marca **Add to Dataset** y selecciona o crea `production-regressions`.
   * Marca **Add Tags** y escribe `needs_review`.
   * Marca **Send Webhook** y proporciona la URL de tu bot de Slack o Sentry.

---

## 7. Buenas Prácticas de Ingeniería

1. **Evitar la Fatiga de Alertas (Alert Fatigue):**
   * No envíes webhooks a canales de alta prioridad por errores menores de formato o concisión. Reserva las alertas sonoras para violaciones de seguridad, fugas de PII o violaciones estrictas de políticas.
2. **Deduplicación en Datasets:**
   * Si 50 usuarios hacen la misma pregunta errónea, evita inundar el dataset con 50 ejemplos idénticos. Agrupa por similitud semántica o hashing de la consulta antes de insertar.
3. **Revisión Humana (Human-in-the-Loop Triage):**
   * Las trazas auto-ingeridas deben contar con un estado de metadatos `status: "pending_review"`. Un curador humano debe proporcionar la respuesta dorada (`ground truth expected output`) antes de que el caso se incorpore al test suite oficial de CI/CD.

---

## 8. Conclusión del Módulo 3

Con la Lección 4 completada, hemos transformado un prototipo de agente en un **sistema de IA robusto de grado de producción**:
* **Módulo 1:** Definición rigurosa de PRD, arquitectura de agentes y contratos de interfaz.
* **Módulo 2:** Datasets de evaluación offline, evaluadores deterministas, heurísticos, semánticos y comparativos (pairwise).
* **Módulo 3:** Telemetría de producción, análisis masivo con Insights Agent, evaluación en streaming (Online Evals) y automatizaciones reactivas que cierran el ciclo del Data Flywheel.
