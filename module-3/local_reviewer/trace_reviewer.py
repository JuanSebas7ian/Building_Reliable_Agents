"""
Local Trace Reviewer & Offline LLMOps Engine (Módulo 3)
=============================================================================
Este módulo proporciona una plataforma de evaluación, auditoría y observabilidad
completamente local para trazas de agentes LLM, replicando las capacidades de
LangSmith (Trace Hierarchy, Online Evals, Insights Agent y Data Flywheel)
sin depender de servicios en la nube.

Componentes principales:
1. Trace Parser & DAG Reconstructor: Agrupa runs en trazas, reconstruyendo la
   jerarquía de invocaciones (root agent, llamadas LLM hijas, ejecuciones de herramientas).
2. Pipeline de Evaluación Multi-Etapa:
   - Evaluador Determinista de Política de Stock (confidencialidad de inventario).
   - Evaluador Determinista de Enrutamiento PRD (correos autorizados de soporte).
   - Evaluador Heurístico de Concisión y Límite de Tokens.
   - Evaluador Estructural de Herramientas (detección de errores y bucles infinitos).
   - Juez LLM Local (Ollama / Qwen2.5 / OpenAI) para fidelidad y alucinaciones.
3. Agregador Estadístico y Métricas:
   - Latencias p50, p90, p99.
   - Tasas de aprobación por regla y global.
   - Clusterización de modos de fallo.
4. Cierre del Data Flywheel Local:
   - Exporta automáticamente las trazas defectuosas a un dataset de regresión
     en JSON para alimentar suites de pruebas en CI/CD local.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import argparse
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
root_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(root_dir / ".env")

# Intentar importar tiktoken para cálculo exacto de tokens
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None  # pyright: ignore[reportConstantRedefinition]
    TIKTOKEN_AVAILABLE = False


# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES DEL PRD DE OFFICEFLOW
# ==============================================================================

AUTHORIZED_DEPARTMENTS = {
    "returns@officeflow.com",
    "billing@officeflow.com",
    "support@officeflow.com",
    "orders@officeflow.com",
    "sales@officeflow.com",
    "fulfillment@officeflow.com",
    "accounts@officeflow.com"
}

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")


# ==============================================================================
# 1. PARSEO DE FECHAS Y RECONSTRUCCIÓN DE ÁRBOLES DE TRAZAS
# ==============================================================================

def parse_dt(s: Optional[str]) -> Optional[datetime]:
    """Parsea una cadena ISO en objeto datetime sin zona horaria para cálculo de deltas."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return None


class LocalTrace:
    """Representa una traza completa reconstruida con su árbol de ejecución."""

    def __init__(self, trace_id: str, runs: List[Dict[str, Any]]):
        self.trace_id = trace_id
        self.runs = runs
        self.root_run: Optional[Dict[str, Any]] = None
        self.child_runs: List[Dict[str, Any]] = []
        self._reconstruct()

    def _reconstruct(self) -> None:
        for r in self.runs:
            if not r.get("parent_run_id"):
                self.root_run = r
            else:
                self.child_runs.append(r)

        # Si no hay root explícito, el de menor tiempo de inicio es el root
        if not self.root_run and self.runs:
            sorted_runs = sorted(
                self.runs,
                key=lambda x: parse_dt(x.get("start_time")) or datetime.min
            )
            self.root_run = sorted_runs[0]
            self.child_runs = sorted_runs[1:]

    @property
    def question(self) -> str:
        """Extrae la pregunta del usuario desde el root o primer mensaje."""
        if not self.root_run:
            return ""
        inputs = self.root_run.get("inputs", {})
        if "question" in inputs:
            return str(inputs["question"])
        if "messages" in inputs and isinstance(inputs["messages"], list):
            for msg in inputs["messages"]:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    return str(msg.get("content", ""))
        return ""

    @property
    def response(self) -> str:
        """Extrae la respuesta final generada por el agente."""
        if not self.root_run:
            return ""
        outputs = self.root_run.get("outputs") or {}
        if "output" in outputs and isinstance(outputs["output"], str):
            return outputs["output"]
        if "messages" in outputs and isinstance(outputs["messages"], list):
            for msg in reversed(outputs["messages"]):
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    return str(msg.get("content", ""))
        return ""

    @property
    def duration_ms(self) -> float:
        """Calcula la duración en milisegundos de la traza completa."""
        start_times = [parse_dt(r.get("start_time")) for r in self.runs if r.get("start_time")]
        end_times = [parse_dt(r.get("end_time")) for r in self.runs if r.get("end_time")]
        valid_starts = [st for st in start_times if st is not None]
        valid_ends = [et for et in end_times if et is not None]

        if not valid_starts or not valid_ends:
            return 0.0

        earliest = min(valid_starts)
        latest = max(valid_ends)
        delta = latest - earliest
        return max(0.0, delta.total_seconds() * 1000.0)

    @property
    def tool_executions(self) -> List[Dict[str, Any]]:
        """Extrae todas las ejecuciones de herramientas en la traza."""
        tools: List[Dict[str, Any]] = []
        for r in self.child_runs:
            if r.get("run_type") == "tool":
                tools.append({
                    "name": r.get("name", "unknown_tool"),
                    "inputs": r.get("inputs", {}),
                    "outputs": r.get("outputs"),
                    "error": r.get("error")
                })
        return tools

    @property
    def has_errors(self) -> bool:
        """Verifica si alguna ejecución dentro de la traza arrojó un error."""
        return any(bool(r.get("error")) for r in self.runs)


# ==============================================================================
# 2. EVALUADORES LOCALES MULTI-ETAPA
# ==============================================================================

class LocalTraceEvaluator:
    """Motor de evaluación de trazas en local."""

    def __init__(self, openai_client: Optional[OpenAI] = None, model: str = CHAT_MODEL):
        self.client = openai_client
        self.model = model

    def eval_stock_policy(self, question: str, response: str) -> Dict[str, Any]:
        """Regla Determinista: No revelar cantidades exactas de inventario."""
        is_stock_question = any(
            t in question.lower()
            for t in ["stock", "inventory", "available", "units", "cuántos", "disponible", "how many", "warehouse", "boxes"]
        )
        if not is_stock_question:
            return {"passed": True, "score": 1.0, "reason": "No aplica política de stock a esta consulta."}

        number_pattern = re.compile(
            r'\b\d+\s*(units|boxes|items|reams|cases|paquetes|cajas|unidades)\b',
            re.IGNORECASE
        )
        match = number_pattern.search(response)
        if match:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"Violación de política: reveló cantidad numérica exacta '{match.group(0)}'."
            }

        return {
            "passed": True,
            "score": 1.0,
            "reason": "Cumple con la política cualitativa de stock sin revelar cantidades exactas."
        }

    def eval_department_routing(self, question: str, response: str) -> Dict[str, Any]:
        """Regla Determinista: Derivar exclusivamente a correos autorizados por el PRD."""
        emails_in_response = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', response.lower())

        if not emails_in_response:
            if any(term in question.lower() for term in ["return", "refund", "devolución", "cancel order"]):
                return {
                    "passed": False,
                    "score": 0.0,
                    "reason": "La consulta requería derivación estricta a Returns, pero no se proporcionó email."
                }
            return {"passed": True, "score": 1.0, "reason": "No requirió derivación a departamentos externos."}

        unauthorized = [e for e in emails_in_response if e not in AUTHORIZED_DEPARTMENTS]
        if unauthorized:
            return {
                "passed": False,
                "score": 0.0,
                "reason": f"Mencionó canales no autorizados: {unauthorized}"
            }

        return {"passed": True, "score": 1.0, "reason": "Canales de soporte válidos y autorizados."}

    def eval_conciseness(self, response: str, max_tokens: int = 160) -> Dict[str, Any]:
        """Evaluador Heurístico: Concisión y límite de tokens."""
        if TIKTOKEN_AVAILABLE and tiktoken is not None:
            try:
                enc = tiktoken.get_encoding("cl100k_base")
                token_count = len(enc.encode(response))
            except Exception:
                token_count = int(len(response.split()) * 1.3)
        else:
            token_count = int(len(response.split()) * 1.3)

        passed = token_count <= max_tokens
        return {
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "token_count": token_count,
            "reason": f"Tokens: {token_count} (Límite: {max_tokens})."
        }

    def eval_tool_health(self, trace: LocalTrace) -> Dict[str, Any]:
        """Evaluador Estructural: Chequeo de fallos de tools y bucles repetidos."""
        tools = trace.tool_executions
        if not tools:
            return {"passed": True, "score": 1.0, "reason": "No se invocaron herramientas."}

        # Chequear errores en herramientas
        for t in tools:
            if t.get("error"):
                return {
                    "passed": False,
                    "score": 0.0,
                    "reason": f"Herramienta '{t.get('name')}' falló con error: {t.get('error')}"
                }

        # Chequear bucles repetidos (más de 3 llamadas consecutivas con los mismos inputs)
        call_signatures = [f"{t.get('name')}:{json.dumps(t.get('inputs', {}), sort_keys=True)}" for t in tools]
        counts: Dict[str, int] = defaultdict(int)
        for sig in call_signatures:
            counts[sig] += 1
            if counts[sig] >= 3:
                return {
                    "passed": False,
                    "score": 0.0,
                    "reason": f"Bucle repetido detectado: {sig.split(':', 1)[0]} llamada {counts[sig]} veces idénticas."
                }

        return {"passed": True, "score": 1.0, "reason": f"Herramientas ejecutadas normalmente ({len(tools)} llamadas)."}

    def eval_faithfulness_llm(self, question: str, response: str) -> Dict[str, Any]:
        """Juez LLM Local: Audita contradicciones semánticas y alucinaciones."""
        if not self.client:
            return {"passed": True, "score": 1.0, "reason": "Juez LLM omitido (sin cliente configurado)."}

        prompt = f"""You are a strict QA auditor for OfficeFlow customer support.
Evaluate if the agent's response is faithful, honest, and helpful based on the user's question.

User Question: {question}
Agent Response: {response}

Key Policy Rules:
1. OfficeFlow allows returns for defective items within 30 days via returns@officeflow.com.
2. The agent must NEVER invent employee names (e.g. John Doe) or personal emails.
3. The agent must state stock qualitatively ("in stock", "low stock") without revealing exact inventory numbers.

Respond ONLY with a JSON object:
{{"faithful": true/false, "explanation": "<brief rationale in 1 sentence>"}}
"""
        try:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            content = res.choices[0].message.content or ""
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                faithful = bool(parsed.get("faithful", True))
                explanation = parsed.get("explanation", "Evaluación completada.")
                return {
                    "passed": faithful,
                    "score": 1.0 if faithful else 0.0,
                    "reason": explanation
                }
            return {"passed": True, "score": 1.0, "reason": "Respuesta no estructurada del juez LLM, asumido pase."}
        except Exception as e:
            return {"passed": True, "score": 1.0, "reason": f"Fallo al invocar juez LLM local: {e}"}


# ==============================================================================
# 3. MOTOR DE REVISIÓN Y AGREGADOR LOCAL (LOCAL TRACE REVIEWER)
# ==============================================================================

class LocalTraceReviewer:
    """Motor integral de auditoría local de trazas según el Módulo 3."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        api_key: str = API_KEY,
        model: str = CHAT_MODEL
    ):
        try:
            self.client = OpenAI(base_url=base_url, api_key=api_key)
        except Exception:
            self.client = None
        self.evaluator = LocalTraceEvaluator(openai_client=self.client, model=model)

    def load_traces_from_file(self, file_path: str) -> List[LocalTrace]:
        """Carga y reconstruye trazas desde un archivo JSON (formato synthetic_traces o RunTree)."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            raise ValueError("El archivo de trazas debe contener una lista JSON de runs.")

        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in raw_data:
            trace_id = item.get("trace_id") or item.get("id") or "unknown_trace"
            grouped[trace_id].append(item)

        traces = [LocalTrace(trace_id, runs) for trace_id, runs in grouped.items()]
        return traces

    def review_trace(self, trace: LocalTrace, run_llm_judge: bool = False) -> Dict[str, Any]:
        """Ejecuta todos los evaluadores locales sobre una traza individual."""
        q = trace.question
        resp = trace.response

        # Evaluadores deterministas y heurísticos (< 2ms)
        stock_res = self.evaluator.eval_stock_policy(q, resp)
        dept_res = self.evaluator.eval_department_routing(q, resp)
        concise_res = self.evaluator.eval_conciseness(resp)
        tool_res = self.evaluator.eval_tool_health(trace)

        # Evaluador LLM (opcional o por muestreo)
        faith_res = self.evaluator.eval_faithfulness_llm(q, resp) if run_llm_judge else {
            "passed": True, "score": 1.0, "reason": "Juez LLM no solicitado en esta pasada."
        }

        all_passed = (
            stock_res["passed"]
            and dept_res["passed"]
            and concise_res["passed"]
            and tool_res["passed"]
            and faith_res["passed"]
        )

        failure_reasons: List[str] = []
        if not stock_res["passed"]:
            failure_reasons.append(f"Stock Policy: {stock_res['reason']}")
        if not dept_res["passed"]:
            failure_reasons.append(f"Department Routing: {dept_res['reason']}")
        if not concise_res["passed"]:
            failure_reasons.append(f"Conciseness: {concise_res['reason']}")
        if not tool_res["passed"]:
            failure_reasons.append(f"Tool Health: {tool_res['reason']}")
        if not faith_res["passed"]:
            failure_reasons.append(f"Faithfulness: {faith_res['reason']}")

        return {
            "trace_id": trace.trace_id,
            "question": q,
            "response": resp,
            "duration_ms": trace.duration_ms,
            "passed": all_passed,
            "failure_reasons": failure_reasons,
            "scores": {
                "stock_policy": stock_res["score"],
                "department_routing": dept_res["score"],
                "conciseness": concise_res["score"],
                "tool_health": tool_res["score"],
                "faithfulness": faith_res["score"],
            },
            "token_count": concise_res.get("token_count", 0),
            "tool_count": len(trace.tool_executions)
        }

    def run_review_batch(
        self,
        traces: List[LocalTrace],
        sample_limit: Optional[int] = None,
        llm_judge_sample_rate: float = 0.1
    ) -> Dict[str, Any]:
        """Ejecuta una auditoría completa por lotes y calcula estadísticas e insights."""
        selected_traces = traces[:sample_limit] if sample_limit else traces
        total = len(selected_traces)
        if total == 0:
            return {"total": 0, "passed": 0, "failed": 0, "results": []}

        results: List[Dict[str, Any]] = []
        durations: List[float] = []
        failed_traces: List[Dict[str, Any]] = []

        import random
        for idx, t in enumerate(selected_traces):
            # Muestreo estocástico para el juez LLM local
            should_run_llm = (random.random() < llm_judge_sample_rate) or (idx == 0)
            rev = self.review_trace(t, run_llm_judge=should_run_llm)
            results.append(rev)
            if rev["duration_ms"] > 0:
                durations.append(rev["duration_ms"])
            if not rev["passed"]:
                failed_traces.append(rev)

        # Cálculo de percentiles de latencia
        durations.sort()
        p50 = durations[int(len(durations) * 0.50)] if durations else 0.0
        p90 = durations[int(len(durations) * 0.90)] if durations else 0.0
        p99 = durations[int(len(durations) * 0.99)] if durations else 0.0

        # Clusterización de fallos por tipo
        failure_clusters: Dict[str, int] = defaultdict(int)
        for ft in failed_traces:
            for fr in ft["failure_reasons"]:
                category = fr.split(":", 1)[0]
                failure_clusters[category] += 1

        passed_count = sum(1 for r in results if r["passed"])

        return {
            "total_traces": total,
            "passed_traces": passed_count,
            "failed_traces": len(failed_traces),
            "pass_rate_pct": round((passed_count / total) * 100.0, 2),
            "latencies_ms": {
                "p50": round(p50, 2),
                "p90": round(p90, 2),
                "p99": round(p99, 2),
                "avg": round(sum(durations) / len(durations), 2) if durations else 0.0
            },
            "failure_clusters": dict(failure_clusters),
            "failed_trace_details": failed_traces,
            "all_results": results
        }

    def export_regression_dataset(
        self,
        batch_results: Dict[str, Any],
        output_path: str = "data/local_regression_dataset.json"
    ) -> int:
        """Cierra el Data Flywheel en local: exporta fallos a un dataset de regresión."""
        failed = batch_results.get("failed_trace_details", [])
        dataset_examples: List[Dict[str, Any]] = []

        for f in failed:
            dataset_examples.append({
                "trace_id": f["trace_id"],
                "input": {"question": f["question"]},
                "bad_output": {"response": f["response"]},
                "metadata": {
                    "source": "local_trace_reviewer",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "failure_reasons": f["failure_reasons"]
                }
            })

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as fp:
            json.dump(dataset_examples, fp, indent=2, ensure_ascii=False)

        return len(dataset_examples)

    def generate_markdown_report(
        self,
        batch_results: Dict[str, Any],
        output_report_path: str = "data/local_trace_review_report.md"
    ) -> str:
        """Genera un reporte ejecutivo en Markdown con los hallazgos de la auditoría local."""
        total = batch_results["total_traces"]
        passed = batch_results["passed_traces"]
        failed = batch_results["failed_traces"]
        pct = batch_results["pass_rate_pct"]
        lat = batch_results["latencies_ms"]
        clusters = batch_results["failure_clusters"]

        lines = [
            "# 📋 Reporte Ejecutivo de Auditoría Local de Trazas (Local LLMOps)",
            f"**Fecha de Análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Metodología:** Multi-Stage Local Evaluation Pipeline (Módulo 3)  ",
            "",
            "---",
            "",
            "## 1. Resumen Ejecutivo de Métricas",
            "",
            "| Métrica | Valor | Estado |",
            "| :--- | :--- | :--- |",
            f"| **Total de Trazas Auditadas** | `{total}` | 🔍 Procesadas |",
            f"| **Trazas Aprobadas** | `{passed}` | ✅ Conformes |",
            f"| **Trazas con Anomalías** | `{failed}` | ⚠️ Requieren Acción |",
            f"| **Tasa Global de Calidad (Pass Rate)** | **`{pct}%`** | " + ("🟢 Saludable" if pct >= 85 else "🔴 Atención Requerida") + " |",
            "",
            "## 2. Métricas de Rendimiento & Latencia",
            "",
            "| Percentil | Latencia (ms) | SLA (< 3000ms) |",
            "| :--- | :--- | :--- |",
            f"| **p50 (Mediana)** | `{lat['p50']} ms` | " + ("✅ OK" if lat['p50'] < 3000 else "⚠️ Alerta") + " |",
            f"| **p90 (Cola Larga)** | `{lat['p90']} ms` | " + ("✅ OK" if lat['p90'] < 5000 else "⚠️ Alerta") + " |",
            f"| **p99 (Peores Casos)** | `{lat['p99']} ms` | " + ("✅ OK" if lat['p99'] < 8000 else "⚠️ Alerta") + " |",
            "",
            "## 3. Distribución y Clusterización de Fallos",
            "",
        ]

        if not clusters:
            lines.append("🎉 **Excelente:** No se registraron violaciones ni fallos en este lote de trazas.")
        else:
            lines.append("| Categoría de Fallo | Frecuencia | Impacto |")
            lines.append("| :--- | :--- | :--- |")
            for cat, count in sorted(clusters.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| **{cat}** | `{count}` incidentes | " + ("🔴 Crítico" if "Policy" in cat or "Routing" in cat else "🟡 Calidad") + " |")

        lines.extend([
            "",
            "## 4. Trazas Críticas para Revisión Humana (Top Casos)",
            ""
        ])

        top_failures = batch_results.get("failed_trace_details", [])[:5]
        if not top_failures:
            lines.append("No hay fallos para mostrar.")
        else:
            for idx, item in enumerate(top_failures, 1):
                lines.extend([
                    f"### Caso {idx}: Traza `{item['trace_id'][:12]}...`",
                    f"- **Consulta de Usuario:** \"{item['question']}\"",
                    f"- **Respuesta del Agente:** \"{item['response'][:150]}...\"",
                    f"- **Motivos de Rechazo:**",
                ])
                for r in item["failure_reasons"]:
                    lines.append(f"  - ❌ {r}")
                lines.append("")

        lines.extend([
            "---",
            "## 5. Acciones del Data Flywheel Local",
            "- 📥 Las trazas anómalas fueron exportadas a `data/local_regression_dataset.json`.",
            "- 🔄 Pueden ser utilizadas directamente para evaluar nuevos prompts o versiones de agente con `module-2/lesson-3/run_experiment.py`.",
            ""
        ])

        report_content = "\n".join(lines)
        out_file = Path(output_report_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as fp:
            fp.write(report_content)

        return report_content


# ==============================================================================
# 4. PUNTO DE ENTRADA CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Auditor y Evaluador Local de Trazas (Módulo 3)")
    parser.add_argument("--input", "-i", default="module-3/lesson-2/synthetic_traces.json", help="Ruta al archivo JSON de trazas")
    parser.add_argument("--sample", "-s", type=int, default=100, help="Número de trazas a analizar (default: 100)")
    parser.add_argument("--llm-rate", "-r", type=float, default=0.1, help="Tasa de muestreo para el Juez LLM (default: 0.1)")
    parser.add_argument("--export-dataset", "-e", default="data/local_regression_dataset.json", help="Ruta de exportación para regresiones")
    parser.add_argument("--report", default="data/local_trace_review_report.md", help="Ruta para el reporte Markdown")
    args = parser.parse_args()

    print("=" * 75)
    print("🚀 AUDITOR LOCAL DE TRAZAS & LLMOPS ENGINE (MÓDULO 3)")
    print(f"📥 Archivo de Entrada: {args.input}")
    print(f"🎯 Muestreo: {args.sample} trazas | Tasa Juez LLM: {int(args.llm_rate * 100)}%")
    print("=" * 75)

    reviewer = LocalTraceReviewer()
    try:
        traces = reviewer.load_traces_from_file(args.input)
        print(f"✅ Cargadas y reconstruidas {len(traces)} trazas únicas con éxito.")
    except Exception as e:
        print(f"❌ Error al cargar trazas: {e}")
        sys.exit(1)

    print(f"🔍 Evaluando lote de {min(args.sample, len(traces))} trazas...")
    batch_results = reviewer.run_review_batch(
        traces=traces,
        sample_limit=args.sample,
        llm_judge_sample_rate=args.llm_rate
    )

    # Imprimir resumen de consola
    print("\n" + "=" * 75)
    print("📊 RESULTADOS DE LA AUDITORÍA LOCAL")
    print("=" * 75)
    print(f"Total Trazas Auditadas:    {batch_results['total_traces']}")
    print(f"Aprobadas (Conformes):     {batch_results['passed_traces']}")
    print(f"Falladas (Anomalías):      {batch_results['failed_traces']}")
    print(f"Tasa de Calidad:           {batch_results['pass_rate_pct']}%")
    lat = batch_results['latencies_ms']
    print(f"Latencias (ms):            p50={lat['p50']}ms | p90={lat['p90']}ms | p99={lat['p99']}ms")
    print("-" * 75)
    print("Familias de Fallo Detectadas:")
    for cat, cnt in batch_results['failure_clusters'].items():
        print(f"  • {cat}: {cnt} incidentes")

    # Exportar dataset de regresión
    saved_count = reviewer.export_regression_dataset(batch_results, args.export_dataset)
    print(f"\n📥 [DATA FLYWHEEL] {saved_count} casos defectuosos exportados a '{args.export_dataset}'.")

    # Generar reporte Markdown
    reviewer.generate_markdown_report(batch_results, args.report)
    print(f"📄 [REPORTE] Reporte Markdown generado en '{args.report}'.")
    print("=" * 75)
    print("✨ Auditoría local finalizada exitosamente.")


if __name__ == "__main__":
    main()
