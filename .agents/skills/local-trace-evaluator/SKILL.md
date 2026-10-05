---
name: local-trace-evaluator
description: "INVOKE THIS SKILL when auditing, reviewing, and evaluating LLM agent traces locally without cloud dependencies. Covers: (1) Reconstructing trace trees from local JSON files, (2) Executing deterministic guardrails, token heuristics, and local LLM judges (Ollama/Qwen/OpenAI), (3) Computing latency percentiles (p50/p90/p99) and failure clusters, (4) Closing the local Data Flywheel by exporting defective runs to regression datasets."
---

# Local Trace Evaluator & Offline LLMOps Skill

This skill provides comprehensive instructions, patterns, and workflows for conducting **local, privacy-preserving trace reviews and evaluations** of AI agents, replicating the core capabilities of **LangSmith** (Trace Hierarchy, Online Evals, Insights Agent, and the Data Flywheel) entirely in a local environment.

---

## 🎯 When to Use This Skill

Activate this skill when:
- The user requests to review or evaluate agent traces locally without sending data to LangSmith Cloud.
- You need to analyze batch traces (such as `synthetic_traces.json` or exported runtime dumps).
- You need to audit compliance against PRD policies (stock confidentiality, routing emails, tool usage loops, token limits).
- You want to compute latency distributions ($p_{50}, p_{90}, p_{99}$) and cluster failure modes.
- You need to curate a regression test suite from failed production/simulation traces to close the **Data Flywheel**.

---

## 🏗️ Core Architecture (Local LLMOps Engine)

```
┌─────────────────────────────────────────────────────────────┐
│                 Input: Local Trace Stream                   │
│   (synthetic_traces.json or live agent execution dumps)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Trace Hierarchy & DAG Parser                  │
│   - Groups runs by `trace_id`                               │
│   - Links child runs (tools, LLMs) to root chain            │
│   - Extracts duration, token count, prompt, final response  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Multi-Stage Local Evaluators (Module 3)            │
│                                                             │
│   1. Deterministic Stock Policy Guardrail (< 2ms, $0.00)    │
│   2. Deterministic Department Routing Guardrail (< 2ms)     │
│   3. Heuristic Token Limit / Conciseness Evaluator (< 1ms)  │
│   4. Structural Tool Error & Loop Detector                  │
│   5. Local LLM-as-Judge (Ollama / Qwen2.5 / OpenAI)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Local Insights & Data Flywheel                │
│   - Executive Markdown Report (`data/*.md`)                 │
│   - Latency Percentiles (p50, p90, p99)                     │
│   - Auto-Curation to `data/local_regression_dataset.json`   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Execution via CLI

The primary tool for local trace auditing is [`module-3/local_reviewer/trace_reviewer.py`](file:///home/juansebas7ian/Proyectos/GitHub/Building_Reliable_Agents/module-3/local_reviewer/trace_reviewer.py).

### 1. Basic Audit (Sample of 50 traces)
```bash
uv run python module-3/local_reviewer/trace_reviewer.py \
  --input module-3/lesson-2/synthetic_traces.json \
  --sample 50
```

### 2. High-Audit Mode (Sample 100 traces with 20% LLM Judge sampling)
```bash
uv run python module-3/local_reviewer/trace_reviewer.py \
  --input module-3/lesson-2/synthetic_traces.json \
  --sample 100 \
  --llm-rate 0.2 \
  --export-dataset data/local_regression_dataset.json \
  --report data/local_trace_review_report.md
```

### CLI Parameters:
* `--input`, `-i`: Path to the input JSON file containing trace runs (default: `module-3/lesson-2/synthetic_traces.json`).
* `--sample`, `-s`: Number of traces to audit (default: `100`).
* `--llm-rate`, `-r`: Sampling probability for invoking the local LLM-as-a-Judge (default: `0.1` / 10%).
* `--export-dataset`, `-e`: Target path for auto-saving failing traces (default: `data/local_regression_dataset.json`).
* `--report`: Target path for the generated executive Markdown report.

---

## 🐍 Programmatic Usage in Python

You can embed the local trace reviewer into custom scripts, CI/CD runners, or unit tests:

```python
from module_3.local_reviewer import LocalTraceReviewer

# Initialize reviewer with local Ollama or OpenAI endpoint
reviewer = LocalTraceReviewer(
    base_url="http://localhost:11434/v1",
    model="qwen2.5:7b"
)

# 1. Load and reconstruct traces
traces = reviewer.load_traces_from_file("module-3/lesson-2/synthetic_traces.json")
print(f"Loaded {len(traces)} traces.")

# 2. Run multi-stage evaluation batch
batch_results = reviewer.run_review_batch(
    traces=traces,
    sample_limit=25,
    llm_judge_sample_rate=0.1
)

# 3. Access metrics
print(f"Pass Rate: {batch_results['pass_rate_pct']}%")
print(f"p50 Latency: {batch_results['latencies_ms']['p50']} ms")
print(f"p99 Latency: {batch_results['latencies_ms']['p99']} ms")

# 4. Export failures to local regression dataset (Closing the Data Flywheel)
reviewer.export_regression_dataset(batch_results, "data/my_regressions.json")

# 5. Generate Markdown Report
reviewer.generate_markdown_report(batch_results, "data/my_report.md")
```

---

## 📋 Evaluation Criteria Explained (Module 3 Compliance)

| Evaluator | Type | Speed | Failure Condition |
| :--- | :--- | :--- | :--- |
| **`eval_stock_policy`** | Deterministic (Regex) | `< 2 ms` | Reveals exact inventory quantities (e.g. *"we have 42 units in stock"*). Must only give qualitative answers. |
| **`eval_department_routing`** | Deterministic (Guardrail) | `< 2 ms` | Mentions unauthorized emails or fails to route returns to `returns@officeflow.com`. |
| **`eval_conciseness`** | Heuristic (Tiktoken) | `< 1 ms` | Response exceeds token limit (default: `> 160 tokens`). |
| **`eval_tool_health`** | Structural | `< 1 ms` | Tool execution threw an unhandled exception or got stuck in a loop (> 3 identical calls). |
| **`eval_faithfulness_llm`** | LLM-as-a-Judge | `~500 ms` | Semantic contradiction with company policy or hallucination of personnel/rules. |

---

## 🔄 Closing the Local Data Flywheel

When failures are found, they are automatically saved into:
`data/local_regression_dataset.json`

Format of each regression item:
```json
{
  "trace_id": "f334ce56-a2bc-4db5-9f14-6a15a92b4e80",
  "input": {
    "question": "Your website's search bar returns no results for anything I type."
  },
  "bad_output": {
    "response": "I'm sorry about the search issue! Contact our Technical Support team at support@officeflow.com..."
  },
  "metadata": {
    "source": "local_trace_reviewer",
    "timestamp": "2026-10-05T09:45:35Z",
    "failure_reasons": [
      "Faithfulness: The agent did not address the user's question about the search bar..."
    ]
  }
}
```

This dataset can be directly ingested into offline evaluation experiments (`module-2/lesson-3/run_experiment.py`) to verify fixes before deploying updated prompts or tools.
