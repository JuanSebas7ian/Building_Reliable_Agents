"""
Módulo 3 - Lección 4: Automations Pipeline & The Data Flywheel
=============================================================================
Este script implementa y demuestra el motor de reglas automáticas (Automations)
en producción para cerrar el ciclo de mejora continua (Data Flywheel).

Capacidades demostradas:
1. Definición de Reglas de Automatización basadas en eventos (Trigger Rules):
   - Alerta por fallo en Online Evals (ej. Stock Policy o Enrutamiento).
   - Alerta por feedback negativo de usuario (Thumbs Down).
   - Alerta por latencia degradada o excepciones en ejecución.
2. Acciones Automáticas ejecutadas por el motor:
   - Auto-etiquetado de trazas en LangSmith (tags: 'needs_human_review', 'policy_violation').
   - Notificación vía Webhook (simulación de Slack / PagerDuty / Sentry).
   - Ingesta automática de la traza fallida en un Dataset de Regresiones ('production-regressions').
3. Cierre del Data Flywheel:
   - Los fallos de producción se transforman automáticamente en casos de prueba
     para ser evaluados offline antes del próximo despliegue.
"""

from typing import Dict, Any, List, Optional
import os
import sys
import json
from datetime import datetime

from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
load_dotenv(root_dir / ".env")

try:
    from langsmith import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    Client = None  # pyright: ignore[reportConstantRedefinition]
    LANGSMITH_AVAILABLE = False


# ==============================================================================
# 1. MODELO DE DATOS Y DEFINICIÓN DE REGLAS DE AUTOMATIZACIÓN
# ==============================================================================

class AutomationRule:
    """Representa una regla automática configurada en LangSmith o en el Gateway."""
    def __init__(
        self,
        name: str,
        condition_description: str,
        tags_to_add: List[str],
        send_webhook: bool,
        add_to_dataset: Optional[str] = None
    ):
        self.name = name
        self.condition_description = condition_description
        self.tags_to_add = tags_to_add
        self.send_webhook = send_webhook
        self.add_to_dataset = add_to_dataset

    def evaluate(self, trace: Dict[str, Any]) -> bool:
        """Determina si una traza cumple las condiciones para disparar la regla."""
        feedback = trace.get("feedback", {})
        metadata = trace.get("metadata", {})
        latency_ms = trace.get("latency_ms", 0)

        # Regla 1: Violación de política de inventario o enrutamiento
        if self.name == "Policy Violation Rule":
            stock_eval = feedback.get("stock_policy_check", {}).get("score", 1.0)
            dept_eval = feedback.get("department_routing_check", {}).get("score", 1.0)
            return bool(stock_eval == 0.0 or dept_eval == 0.0)

        # Regla 2: Feedback negativo del usuario final (Thumbs Down)
        if self.name == "User Dislike Rule":
            user_score = feedback.get("user_feedback", {}).get("score")
            return bool(user_score is not None and user_score == 0)

        # Regla 3: Alucinación o falta de fidelidad semántica
        if self.name == "Faithfulness Hallucination Rule":
            faith_score = feedback.get("context_faithfulness", {}).get("score")
            return bool(faith_score is not None and faith_score == 0.0)

        # Regla 4: SLA de latencia degradada (> 5000 ms)
        if self.name == "High Latency SLA Rule":
            return bool(latency_ms > 5000)

        return False


# ==============================================================================
# 2. MOTOR DE EJECUCIÓN DE AUTOMATIZACIONES (ACTIONS ENGINE)
# ==============================================================================

class AutomationsEngine:
    """Motor que procesa trazas y ejecuta acciones automáticas."""

    def __init__(self, client: Optional[Any] = None):
        self.client = client
        self.rules: List[AutomationRule] = []
        self.notification_log: List[Dict[str, Any]] = []
        self.curated_dataset_items: List[Dict[str, Any]] = []

    def register_rule(self, rule: AutomationRule) -> None:
        self.rules.append(rule)

    def trigger_webhook_alert(self, rule_name: str, trace_id: str, reason: str) -> None:
        """Simula el envío de una alerta a Slack o PagerDuty."""
        payload = {
            "channel": "#alerts-agent-production",
            "timestamp": datetime.now().isoformat(),
            "rule": rule_name,
            "run_id": trace_id,
            "severity": "CRITICAL" if "Policy" in rule_name else "WARNING",
            "message": f"🚨 [AUTOMATION TRIGGERED] {rule_name}: {reason}"
        }
        self.notification_log.append(payload)
        print(f"    📢 [WEBHOOK NOTIFY] -> Enviado a {payload['channel']}: {payload['message']}")

    def add_to_langsmith_dataset(
        self,
        dataset_name: str,
        question: str,
        response: str,
        failure_reason: str
    ) -> None:
        """Añade el caso fallido a un dataset para cerrar el Data Flywheel."""
        dataset_entry = {
            "dataset": dataset_name,
            "input": {"question": question},
            "output": {"ground_truth_fix_needed": True, "bad_response": response},
            "metadata": {"added_by": "langsmith_automation", "failure_reason": failure_reason}
        }
        self.curated_dataset_items.append(dataset_entry)

        if self.client and hasattr(self.client, "create_example"):
            try:
                # Comprobar si existe el dataset o crearlo
                datasets = list(self.client.list_datasets(dataset_name=dataset_name))
                if not datasets:
                    dataset = self.client.create_dataset(
                        dataset_name=dataset_name,
                        description="Casos fallidos capturados automáticamente desde producción por reglas de automatización."
                    )
                else:
                    dataset = datasets[0]

                self.client.create_example(
                    inputs={"question": question},
                    outputs={"expected": "Respuesta corregida pendiente de revisión humana."},
                    metadata={"failure_reason": failure_reason, "source": "automation_flywheel"},
                    dataset_id=dataset.id
                )
                print(f"    📥 [LANGSMITH DATASET] Caso exportado al dataset '{dataset_name}' exitosamente.")
            except Exception as e:
                print(f"    ⚠️ [LANGSMITH DATASET] No se pudo escribir al dataset remoto: {e}")
        else:
            print(f"    📥 [MOCK DATASET] Caso agregado al dataset local de regresiones '{dataset_name}'.")

    def process_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa todas las reglas sobre una traza y ejecuta las acciones pertinentes."""
        run_id = trace.get("run_id", "unknown_run")
        question = trace.get("inputs", {}).get("question", "")
        response = trace.get("outputs", {}).get("response", "")
        tags = list(trace.get("tags", []))

        triggered_rules: List[str] = []

        print(f"\n===========================================================================")
        print(f"🤖 [AUTOMATIONS ENGINE] Analizando Traza: {run_id}")
        print(f"📥 Pregunta: '{question}'")
        print(f"📤 Respuesta: '{response[:90]}...'")
        print(f"---------------------------------------------------------------------------")

        for rule in self.rules:
            if rule.evaluate(trace):
                triggered_rules.append(rule.name)
                print(f"  🔥 Disparada Regla: '{rule.name}' ({rule.condition_description})")

                # 1. Acción: Añadir Etiquetas (Tags)
                for tag in rule.tags_to_add:
                    if tag not in tags:
                        tags.append(tag)
                        print(f"    🏷️ [TAG APPLIED] +'{tag}'")

                # 2. Acción: Disparar Alerta Webhook
                if rule.send_webhook:
                    reason = str(trace.get("feedback", {}))
                    self.trigger_webhook_alert(rule.name, run_id, reason)

                # 3. Acción: Añadir al Dataset de Regresiones (Data Flywheel)
                if rule.add_to_dataset:
                    self.add_to_langsmith_dataset(
                        rule.add_to_dataset,
                        question=question,
                        response=response,
                        failure_reason=rule.condition_description
                    )

        if not triggered_rules:
            print(f"  ✅ Ninguna regla de anomalía disparada. La traza cumple todos los estándares.")

        # Actualizar tags en LangSmith si el cliente está disponible
        if self.client and hasattr(self.client, "update_run") and triggered_rules:
            try:
                self.client.update_run(run_id=run_id, tags=tags)
                print(f"    ☁️ [LANGSMITH SYNC] Tags sincronizados en LangSmith: {tags}")
            except Exception:
                pass

        return {
            "run_id": run_id,
            "triggered_rules": triggered_rules,
            "final_tags": tags
        }


# ==============================================================================
# 3. DEMOSTRACIÓN PRÁCTICA DEL DATA FLYWHEEL
# ==============================================================================

def run_automations_demonstration() -> None:
    print("=" * 75)
    print("MÓDULO 3 - LECCIÓN 4: AUTOMATIONS & THE DATA FLYWHEEL")
    print("Cerrando el Ciclo de Mejora Continua en Producción")
    print("=" * 75)

    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    client = None
    if LANGSMITH_AVAILABLE and Client is not None and langchain_api_key:
        try:
            client = Client()
            print(" Connected to LangSmith Client (Automations Live Mode).")
        except Exception:
            print("⚠️ Running in Local/Simulation Automations Mode.")
    else:
        print("💡 Running in Local/Simulation Automations Mode.")

    # 1. Instanciar Motor de Automatizaciones
    engine = AutomationsEngine(client=client)

    # 2. Registrar Reglas de Producción
    engine.register_rule(
        AutomationRule(
            name="Policy Violation Rule",
            condition_description="Fallo de política de stock o enrutamiento de departamentos",
            tags_to_add=["policy_breach", "needs_human_review"],
            send_webhook=True,
            add_to_dataset="production-regressions"
        )
    )

    engine.register_rule(
        AutomationRule(
            name="User Dislike Rule",
            condition_description="Usuario final presionó Thumbs Down",
            tags_to_add=["user_negative_feedback", "triage_support"],
            send_webhook=True,
            add_to_dataset="production-regressions"
        )
    )

    engine.register_rule(
        AutomationRule(
            name="Faithfulness Hallucination Rule",
            condition_description="Evaluador LLM detectó contradicción semántica con el contexto",
            tags_to_add=["hallucination_detected", "eval_failure"],
            send_webhook=False,
            add_to_dataset="production-regressions"
        )
    )

    engine.register_rule(
        AutomationRule(
            name="High Latency SLA Rule",
            condition_description="Latencia total superior al SLA de 5000ms",
            tags_to_add=["latency_sla_breach"],
            send_webhook=True,
            add_to_dataset=None
        )
    )

    # 3. Flujo de Trazas Simuladas de Producción
    production_stream: List[Dict[str, Any]] = [
        # Caso 1: Consulta limpia y exitosa
        {
            "run_id": "run_prod_101_ok",
            "latency_ms": 1150,
            "inputs": {"question": "What is the return window for defective stationery?"},
            "outputs": {"response": "All defective stationery items can be returned within 30 days by emailing returns@officeflow.com."},
            "tags": ["production", "v2.1"],
            "feedback": {
                "stock_policy_check": {"score": 1.0},
                "department_routing_check": {"score": 1.0},
                "context_faithfulness": {"score": 1.0},
                "user_feedback": {"score": 1}  # Thumbs up
            }
        },
        # Caso 2: Violación de Política de Stock
        {
            "run_id": "run_prod_102_leak",
            "latency_ms": 1420,
            "inputs": {"question": "How many executive pens do you have right now?"},
            "outputs": {"response": "We have 150 units of executive pens in aisle 4."},
            "tags": ["production", "v2.1"],
            "feedback": {
                "stock_policy_check": {"score": 0.0},
                "department_routing_check": {"score": 1.0},
                "context_faithfulness": {"score": 1.0}
            }
        },
        # Caso 3: Alucinación + Descontento de Usuario (Thumbs Down)
        {
            "run_id": "run_prod_103_bad",
            "latency_ms": 2100,
            "inputs": {"question": "Can I replace an open pack of markers?"},
            "outputs": {"response": "No, open packs cannot be returned under any condition whatsoever."},
            "tags": ["production", "v2.1"],
            "feedback": {
                "stock_policy_check": {"score": 1.0},
                "department_routing_check": {"score": 1.0},
                "context_faithfulness": {"score": 0.0},  # Alucinación: el PRD sí lo permite si están defectuosos
                "user_feedback": {"score": 0}  # Thumbs down
            }
        },
        # Caso 4: Degradación Severa de Latencia
        {
            "run_id": "run_prod_104_slow",
            "latency_ms": 7820,
            "inputs": {"question": "Give me a summary of all catalog prices."},
            "outputs": {"response": "Here is the summary of items..."},
            "tags": ["production", "v2.1"],
            "feedback": {
                "stock_policy_check": {"score": 1.0},
                "department_routing_check": {"score": 1.0},
                "context_faithfulness": {"score": 1.0}
            }
        }
    ]

    # 4. Procesar el Stream a través del Motor de Automatizaciones
    results = [engine.process_trace(t) for t in production_stream]

    # 5. Resumen del Cierre del Data Flywheel
    print("\n" + "=" * 75)
    print("🔄 RESUMEN DEL DATA FLYWHEEL (CICLO CERRADO DE PRODUCCIÓN)")
    print("=" * 75)
    print(f"📊 Total de Trazas Auditadas:     {len(results)}")
    print(f"🚨 Alertas Webhook Emitidas:      {len(engine.notification_log)}")
    print(f"📥 Casos Ingeridos a Dataset:     {len(engine.curated_dataset_items)} ejemplos en 'production-regressions'")
    print("-" * 75)
    print("Lista de Ejemplos Nuevos para Evaluación Offline (CI/CD):")
    for idx, item in enumerate(engine.curated_dataset_items, 1):
        q = item['input']['question']
        reason = item['metadata']['failure_reason']
        print(f"  {idx}. [{item['dataset']}] Pregunta: \"{q}\"")
        print(f"     Motivo de Captura: {reason}")

    print("=" * 75)
    print("🎉 Pipeline de Automatizaciones completado con éxito.")
    print("👉 Revisa CLASE_MAGISTRAL_LECCION_4.md para profundizar en el Data Flywheel.")


if __name__ == "__main__":
    run_automations_demonstration()
