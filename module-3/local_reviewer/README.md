# Local Reviewer: Motor de Auditoría y Observabilidad Local (Módulo 3)

Este paquete implementa una plataforma de evaluación, auditoría y análisis de trazas de agentes LLM **completamente local**, que replica de forma fiel las capacidades de **LangSmith** (jerarquía de trazas, online evals, insights agent y data flywheel) sin enviar datos a la nube.

---

## 🚀 Inicio Rápido

Para auditar un lote de trazas (por ejemplo, las trazas sintéticas de OfficeFlow):

```bash
uv run python module-3/local_reviewer/trace_reviewer.py --sample 50 --llm-rate 0.15
```

### Argumentos CLI Disponibles

* `--input`, `-i`: Ruta del archivo JSON con runs/trazas (por defecto: `module-3/lesson-2/synthetic_traces.json`).
* `--sample`, `-s`: Cantidad de trazas a muestrear (por defecto: `100`).
* `--llm-rate`, `-r`: Proporción de muestreo para el Juez LLM local (por defecto: `0.1` = 10%).
* `--export-dataset`, `-e`: Archivo destino para exportar las trazas fallidas (por defecto: `data/local_regression_dataset.json`).
* `--report`: Archivo destino para el reporte ejecutivo en Markdown (por defecto: `data/local_trace_review_report.md`).

---

## 🛠️ Arquitectura de Evaluadores

1. **`eval_stock_policy` (Determinista):** Verifica que el agente no filtre números exactos de inventario.
2. **`eval_department_routing` (Determinista):** Asegura el cumplimiento de los canales de correo del PRD.
3. **`eval_conciseness` (Heurístico):** Controla el límite de tokens para evitar respuestas sobrecargadas.
4. **`eval_tool_health` (Estructural):** Monitorea excepciones no capturadas y previene bucles de herramientas.
5. **`eval_faithfulness_llm` (Semántico):** Juez LLM local (Ollama / Qwen2.5 / OpenAI) que detecta alucinaciones y respuestas evasivas.

---

## 🔄 Cierre del Data Flywheel Local

Las trazas que no pasan todos los filtros se guardan automáticamente en:
`data/local_regression_dataset.json`

Permitiendo retroalimentar las suites de pruebas de CI/CD del agente sin intervención manual.
