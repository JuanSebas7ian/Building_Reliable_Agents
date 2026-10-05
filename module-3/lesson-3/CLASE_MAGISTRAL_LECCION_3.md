# Clase Magistral: Lección 3 — Online Evals (Evaluación Continua en Streaming de Trazas)

> **Módulo 3: Moving Towards Production**  
> **Tema:** Monitoreo Continuo, Evaluadores Asíncronos en Tiempo Real y Cierre del Ciclo de Calidad en Producción.  
> **Código Asociado:** [`online_evals.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/online_evals.py)

---

## 1. El Dilema de Producción: ¿Offline vs. Online Evals?

Hasta el **Módulo 2**, todo el marco de evaluación operaba en modo **Offline (Batch)**:
* Teníamos un dataset estático predefinido (`officeflow-eval-golden-v1`).
* Ejecutábamos experimentos deliberados (`evaluate()`) comparando versiones de agentes (`agent_v0` vs `agent_v3`).
* Medíamos métricas agregadas antes de aprobar un Pull Request.

Sin embargo, cuando un agente se despliega a usuarios reales:
1. **Distribución Dinámica de Consultas (Data Drift):** Los usuarios formulan preguntas que los ingenieros nunca anticiparon en los datasets de prueba.
2. **Latencia Crítica del Usuario:** No podemos ejecutar un LLM Judge de 4 segundos dentro del ciclo de solicitud/respuesta (`request-response cycle`) del usuario, porque duplicaría el tiempo percibido.
3. **Presupuesto y Costes de API:** Si evaluamos el 100% del tráfico con modelos pesados como `gpt-4o`, el coste de observabilidad superará el coste del propio agente.

Aquí nacen las **Online Evals (Evaluaciones en Vivo / Streaming)**: mecanismos asíncronos que auditan las trazas de producción en tiempo real conforme fluyen por el sistema.

---

## 2. Arquitectura de Online Evals

El patrón recomendado para Online Evals desacopla la interacción del usuario de la evaluación:

```mermaid
flowchart TD
    User([Usuario Final]) -->|1. Prompt| Gateway[API / Servidor de Aplicación]
    Gateway -->|2. Inferencia Streaming| Agent[Agente LangGraph / OpenAI]
    Agent -->|3. Respuesta Inmediata| User
    
    Gateway -.->|4. Traza Asíncrona (Background)| LS[LangSmith Platform]
    
    subgraph "Online Evals Pipeline (Asíncrono)"
        LS -->|Webhook / Event Stream| Queue[Cola de Evaluación]
        Queue --> DetRule1[Regla Determinista: Stock Policy (<2ms, $0)]
        Queue --> DetRule2[Regla Determinista: Routing PRD (<2ms, $0)]
        Queue --> DetRule3[Regla Determinista: Conciseness (<1ms, $0)]
        Queue -->|Sampling 5% - 10%| LLMJudge[LLM Judge: Faithfulness / Hallucination]
    end
    
    DetRule1 --> Feedback[LangSmith client.create_feedback]
    DetRule2 --> Feedback
    DetRule3 --> Feedback
    LLMJudge --> Feedback
    Feedback --> Dashboard[(Dashboard de Producción & Métricas)]
```

### Características Clave:
* **Zero User Latency:** La evaluación ocurre fuera de la ruta crítica del usuario. El usuario recibe su respuesta inmediatamente.
* **Trazabilidad Unificada:** Las puntuaciones (`scores`) y justificaciones (`reasons`) se asocian directamente al `run_id` de la traza original mediante el endpoint de `Feedback`.

---

## 3. Taxonomía de Evaluadores en Línea

Para maximizar la cobertura sin disparar los costos, se implementa una **estrategia piramidal de 3 capas**:

| Nivel | Tipo de Evaluador | Latencia | Coste ($) | Frecuencia de Muestreo | Ejemplo en OfficeFlow |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Capa 1** | **Deterministas (Regex / Heurísticos)** | `< 2 ms` | **$0.00** | **100% de las trazas** | Regla de Confidencialidad de Stock (`eval_online_stock_policy`). |
| **Capa 2** | **Guardrails Estructurales** | `< 5 ms` | **$0.00** | **100% de las trazas** | Derivación a Correos Autorizados (`eval_online_department_routing`). |
| **Capa 3** | **LLM Judges Semánticos** | `500 - 2000 ms` | Variable | **Muestreo (5% a 20%)** | Detección de Alucinación / Fidelidad (`eval_online_faithfulness_judge`). |

---

## 4. Desglose del Código: `online_evals.py`

En el script [`online_evals.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/lesson-3/online_evals.py), implementamos el pipeline completo:

### A. Regla Determinista de Política de Stock (Zero Cost)
```python
def eval_online_stock_policy(question: str, response: str) -> Dict[str, Any]:
    # Si el usuario pregunta por inventario, prohibir que el agente revele cantidades exactas:
    number_pattern = re.compile(r'\b\d+\s*(units|boxes|items|reams|cases|paquetes|cajas|unidades)\b', re.IGNORECASE)
    match = number_pattern.search(response)
    if match:
        return {"passed": False, "score": 0.0, "reason": f"Violación: reveló cantidad exacta '{match.group(0)}'."}
    return {"passed": True, "score": 1.0, "reason": "Cumple política cualitativa."}
```

### B. Regla Determinista de Enrutamiento Autorizado (PRD Compliance)
```python
AUTHORIZED_DEPARTMENTS = {
    "returns@officeflow.com",
    "billing@officeflow.com",
    "support@officeflow.com",
    "orders@officeflow.com"
}

def eval_online_department_routing(question: str, response: str) -> Dict[str, Any]:
    emails_in_response = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', response.lower())
    unauthorized = [e for e in emails_in_response if e not in AUTHORIZED_DEPARTMENTS]
    if unauthorized:
        return {"passed": False, "score": 0.0, "reason": f"Mencionó canales no autorizados: {unauthorized}"}
    return {"passed": True, "score": 1.0, "reason": "Canales autorizados."}
```

### C. Emisión de Feedback a LangSmith
```python
def log_online_feedback_to_langsmith(client, run_id, results):
    for metric_name, res in results.items():
        client.create_feedback(
            run_id=run_id,
            key=metric_name,
            score=res["score"],
            comment=res["reason"],
            source_info={"source": "online_eval_stream"}
        )
```

---

## 5. Simulación de Trazas en Vivo y Detección de Anomalías

Al ejecutar el script con trazas simuladas:
1. **`run_prod_001_clean`**: Pasa todos los filtros. Consulta normal de resmas de papel.
2. **`run_prod_002_violation`**: Alerta disparada. Revela: *"We currently have exactly 42 boxes in stock"*. Violación de política de stock.
3. **`run_prod_003_bad_routing`**: Alerta disparada. Revela un correo personal no autorizado: *"john.doe@gmail.com"*. Violación de enrutamiento y alucinación.

---

## 6. Configuración de Online Evaluators en LangSmith Platform

En la interfaz de LangSmith, las Online Evals se configuran bajo el menú **Projects -> Rules / Online Evaluators**:
1. **Target Project:** Selecciona el proyecto de producción (ej. `officeflow-agent-prod`).
2. **Sampling Rate:** Define la tasa de muestreo (ej. `10%` para evaluadores LLM, `100%` para reglas de código).
3. **Filter Expression:** Opcionalmente aplica filtros (ej. `eq(tags, "production") and has(outputs, "error")`).
4. **Evaluator Type:** Puede ser un prompt predeterminado en el Prompt Hub o un endpoint webhook propio.

---

## 7. Resumen y Siguiente Paso

Las Online Evals son los **ojos y oídos del sistema en producción**. No evitan que el fallo ocurra en la milésima de segundo en que se genera, pero lo detectan y etiquetan inmediatamente.

En la **Lección 4 (Automations)**, veremos cómo reaccionar ante estas alertas de forma automática: disparar webhooks, etiquetar trazas defectuosas para revisión humana y agregarlas directamente al dataset de regresiones para reentrenar y evaluar al agente.
