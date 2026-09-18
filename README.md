# Building Reliable Agents - Python

## Introducción

Bienvenido a la carpeta de trabajo del curso de LangChain Academy: **Building Reliable Agents** (LangSmith Professional).

Este repositorio contiene las implementaciones en Python de cada módulo del curso, acompañadas de sus respectivos archivos de documentación técnica (`.md`) en español que detallan la arquitectura, teoría y pasos de ejecución.

### 📚 Índice de Scripts (`.py`) y sus Documentos Informativos (`.md`)

| Componente / Módulo | Script Python (`.py`) | Documento Informativo (`.md`) | Descripción |
| :--- | :--- | :--- | :--- |
| **Diagnóstico de Entorno** | [`env_utils.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/env_utils.py) | [`env_utils.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/env_utils.md) | Comprobación de versiones, venv y API keys. |
| **Agente OfficeFlow** | [`officeflow-agent/agent_v0.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v0.py) | [`officeflow-agent/agent_v0.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v0.md) | Agente base con OpenAI Tools sin observabilidad. |
| | [`officeflow-agent/agent_v1.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v1.py) | [`officeflow-agent/agent_v1.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v1.md) | Instrumentación con LangSmith Tracing y UUIDv7. |
| | [`officeflow-agent/agent_v2.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v2.py) | [`officeflow-agent/agent_v2.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v2.md) | Descubrimiento de esquema SQL en prompt de herramienta. |
| | [`officeflow-agent/agent_v3.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v3.py) | [`officeflow-agent/agent_v3.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v3.md) | Política de bandas de stock para cumplir con PRD. |
| | [`officeflow-agent/agent_v4.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v4.py) | [`officeflow-agent/agent_v4.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v4.md) | No-Chunking RAG con documentos de políticas completos. |
| | [`officeflow-agent/agent_v5.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v5.py) | [`officeflow-agent/agent_v5.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v5.md) | Optimización de concisión y ahorro de tokens. |
| | [`officeflow-agent/knowledge_base/generate_embeddings.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/knowledge_base/generate_embeddings.py) | [`officeflow-agent/knowledge_base/generate_embeddings.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/knowledge_base/generate_embeddings.md) | Generación y caché de vectores de embeddings. |
| **Módulo 1: Observation** | [`module-1/lesson-2/third_party_agent.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-1/lesson-2/third_party_agent.py) | [`module-1/lesson-2/third_party_agent.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-1/lesson-2/third_party_agent.md) | Agente con llamadas a herramientas nativas OpenAI. |
| | [`module-1/lesson-2/thread_agent.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-1/lesson-2/thread_agent.py) | [`module-1/lesson-2/thread_agent.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-1/lesson-2/thread_agent.md) | Agente con memoria persistente y threads trazables. |
| | *Lección 3 del Curso* | [`module-1/lesson-3/ANALYZING_YOUR_AGENT.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-1/lesson-3/ANALYZING_YOUR_AGENT.md) | Guía de diagnóstico de trazas y escenarios PRD. |
| **Módulo 2: Evaluation** | [`module-2/token_utils.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/token_utils.py) | - | Módulo central de tokenización (`tiktoken`) y métricas de concisión. |
| | [`module-2/lesson-1/evaluating_agents.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-1/evaluating_agents.py) | [`module-2/lesson-1/EVALUATING_AGENTS.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-1/EVALUATING_AGENTS.md) | Fundamentos de evaluación, Flywheel y telemetría de tokens y latencia. |
| | `module-2/lesson-2/officeflow-dataset.csv` & [`module-2/lesson-2/upload_dataset.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/upload_dataset.py) | [`module-2/lesson-2/datasets_guide.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/datasets_guide.md) | Creación y subida automatizada del dataset de pruebas a LangSmith. |
| | [`module-2/lesson-3/run_experiment.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-3/run_experiment.py) | [`module-2/lesson-3/run_experiment.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-3/run_experiment.md) | Orquestación de experimentos con Dummy App y Agente Emma real. |
| | [`module-2/lesson-4/eval_schema_check.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_schema_check.py) & [`eval_stock_policy.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_stock_policy.py) & [`run_eval.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/run_eval.py) | [`module-2/lesson-4/run_eval.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/run_eval.md) | Evaluadores deterministas (esquema SQL y confidencialidad de stock). |
| | [`module-2/lesson-5/eval_llm_judge.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/eval_llm_judge.py) & [`run_experiment.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/run_experiment.py) | [`module-2/lesson-5/run_experiment.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-5/run_experiment.md) | Evaluación cualitativa con LLM-as-a-Judge (Ollama / OpenAI). |
| | [`module-2/lesson-6/eval_conciseness_pairwise.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-6/eval_conciseness_pairwise.py) & [`run_pairwise_experiment.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-6/run_pairwise_experiment.py) | [`module-2/lesson-6/eval_conciseness_pairwise.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-6/eval_conciseness_pairwise.md) | Evaluación pareada A/B de concisión (v4 vs v5) con tokens. |
| | *Guía de Arquitectura de Evaluación* | [`module-2/EVALUATION_APPROACHES.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/EVALUATION_APPROACHES.md) | Guía oficial LangSmith: Evaluación de respuesta final, pasos y trayectorias. |
| **Módulo 3: Production** | [`module-3/lesson-2/generate_traces.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-3/lesson-2/generate_traces.py) | [`module-3/lesson-2/generate_traces.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-3/lesson-2/generate_traces.md) | Generación de trazas sintéticas a escala. |
| | [`module-3/lesson-2/upload_traces.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-3/lesson-2/upload_traces.py) | [`module-3/lesson-2/upload_traces.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-3/lesson-2/upload_traces.md) | Ingesta masiva con desplazamiento de fechas. |

---

## 🚀 Setup

### Prerequisites

- The Chrome browser is recommended
- Ensure you're using Python >=3.12, <=3.13 [More info](#python-virtual-environments)
- A package/project manager: [uv](https://docs.astral.sh/uv/) (recommended) or [pip](https://pypi.org/project/pip/)

### Installation

Download the course repository
```bash
# Clone the repo (shallow — latest code only)
git clone --depth 1 https://github.com/langchain-ai/lca-reliable-agents.git
cd lca-reliable-agents/python
```

Make a copy of example.env
```bash
# Create .env file
cp example.env .env
```

Edit the .env file to include the keys below. [More info](#model-providers)
```bash
# Required
OPENAI_API_KEY='your_openai_api_key_here'

# Optional, used by the question generator
ANTHROPIC_API_KEY='your_anthropic_api_key_here'

# Required for evaluation and tracing
LANGSMITH_API_KEY='your_langsmith_api_key_here'
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=lca-reliable-agents
# Uncomment the following if you are on the EU instance:
#LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

Create a [LangSmith](https://smith.langchain.com/) account and API Key.  
Get and OpenAI API Key [here](https://openai.com/index/openai-api/).  
Optional, an Anthropic API Key [here](https://console.anthropic.com)  

Make a virtual environment and install dependencies. [More info](#python-virtual-environments)

<details open>
<summary>Using uv (recommended)</summary>

```bash
uv sync
```

</details>

<details>
<summary>Using pip</summary>

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

</details>

### Setup Verification

After completing the Setup section, we recommend you run this command to verify your environment:

<details open>
<summary>Using uv</summary>

```bash
uv run python env_utils.py
```

</details>

<details>
<summary>Using pip</summary>

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python env_utils.py
```

</details>


[If the script flags issues, see this section below.](#setup-verification-issues)

### Running Scripts

This course uses Python scripts (not notebooks).

<details open>
<summary>Using uv (recommended)</summary>

```bash
# Example: run the agent interactively
uv run python officeflow-agent/agent_v5.py

# Example: run an experiment
uv run python module-2/lesson-3/run_experiment.py
```

</details>

<details>
<summary>Using pip</summary>

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Example: run the agent interactively
python officeflow-agent/agent_v5.py

# Example: run an experiment
python module-2/lesson-3/run_experiment.py
```

</details>

### If you are using coding agents in the course

You can provide your agent access to the LangSmith Documents. The instructions are [here](https://docs.langchain.com/use-these-docs).


## 🎓 Lessons

### OfficeFlow Agent

The course builds an iterative customer support agent (versions v0–v6) for OfficeFlow Supply Co., with tools for database queries and knowledge base search.

### Module 1: Observation

- **Lesson 1 — Observability.** Why traditional debugging falls short for AI agents and how observability tools fill the gap.
- **Lesson 2 — Tracing with LangSmith.** Instrument your agent so every LLM call, tool invocation, and decision is captured in a trace.
- **Lesson 3 — Analyzing your Agent.** Use traces to run through PRD scenarios, spot failures, and iteratively debug your agent across multiple versions.

### Module 2: Evaluation

- **Lesson 1 — Evaluating Agents.** Why you need automated evals to monitor agent quality over time and detect regression as you develop.
- **Lesson 2 — Creating Datasets.** Build collections of test inputs and reference outputs for repeatable evaluation.
- **Lesson 3 — Running Experiments.** Connect a target, a dataset, and evaluators to run your first experiment in LangSmith.
- **Lesson 4 — Eval 1 - Code-based Eval.** Write deterministic evaluators that work like unit tests — checking tool usage, output shape, and keyword matching.
- **Lesson 5 — Eval 2 - LLM-as-Judge.** Use an LLM to evaluate subjective criteria that are hard to test with code alone.
- **Lesson 6 — Eval 3 - Pairwise Evaluations.** Compare two agent versions side by side to measure which performs better.

### Module 3: Moving Towards Production

- **Lesson 1 — Moving Towards Production.** Transition from internal testing to real users, and learn the techniques needed to observe and evaluate at scale.
- **Lesson 2 — Insights Agent.** Automatically analyze traces at scale to detect usage patterns and failure modes across hundreds of traces.
- **Lesson 3 — Online Evals.** Automatically score every production trace as it comes in, giving you continuous signal on agent quality.

## 📖 Related Resources

### Setup Verification Issues
**What the verification checks:**
- ✅ Python executable location and version (must be >=3.12, <=3.13)
- ✅ Virtual environment is properly activated
- ✅ Required packages are installed with correct versions
- ✅ Packages are in the correct Python version's site-packages
- ✅ Environment variables (API keys) are properly configured

**Configuration Issues and Solutions:**

<details>
<summary>ImportError when running env_utils.py</summary>

If you see an error like `ModuleNotFoundError: No module named 'dotenv'`, you're likely running Python outside the virtual environment.

**Solution:**
- Use `uv run python xxx.py` (recommended), or
- Activate the virtual environment first:
  - macOS/Linux: `source .venv/bin/activate`
  - Windows: `.venv\Scripts\activate`

</details>

<details>
<summary>Environment Variable Conflicts</summary>

If you see a warning about "ENVIRONMENT VARIABLE CONFLICTS DETECTED", you have API keys set in your system environment that differ from your .env file. Since `load_dotenv()` doesn't override existing variables by default, your system values will be used.

**Solutions:**
1. Unset the conflicting system environment variables (commands provided in warning)
2. Use `load_dotenv(override=True)` in your scripts to force .env values to take precedence
3. Update your .env file to match your system environment

</details>

<details>
<summary>LangSmith Tracing Errors</summary>

If you see "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY still has the example/placeholder value", you need to set a valid LangSmith API key in your .env file.

</details>

<details>
<summary>Wrong Python Version</summary>

If you see a warning about Python version not satisfying requirements, you need Python >=3.12 and <=3.13.

**Solution:**
- If using `uv`: Run `uv sync` which will automatically install the correct Python version
- If using pip: Install Python 3.12 or 3.13 using [pyenv](#python-virtual-environments) or from [python.org](https://www.python.org/downloads/)

</details>



### Python Virtual Environments

Managing your Python version is often best done with virtual environments. This allows you to select a Python version for the course independent of the system Python version.

<details open>
<summary>Using uv (recommended)</summary>

`uv` will install a version of Python compatible with the versions specified in the `pyproject.toml` in the `.venv` directory when running the `uv sync` specified above. It will use this version when invoking with `uv run`. For additional information, please see [uv](https://docs.astral.sh/uv/).
</details>

<details>
<summary>Using pyenv + pip</summary>

If you are using pip instead of uv, you may prefer using pyenv to manage your Python versions. For additional information, please see [pyenv](https://github.com/pyenv/pyenv).

```bash
pyenv install 3.13
pyenv local 3.13
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

</details>

### Model Providers

If you don't have an OpenAI API key, you can sign up [here](https://openai.com/index/openai-api/). The course primarily uses gpt-5-nano which is very inexpensive.
You may also obtain additional API keys for [Anthropic](https://console.anthropic.com).

This course has been created using particular models and model providers.  You can use other providers, but you will need to update the API keys in the .env file and make some necessary code changes. LangChain supports many chat model providers [here](https://docs.langchain.com/oss/python/integrations/providers/all_providers).

### Getting Started with LangSmith

- Create a [LangSmith](https://smith.langchain.com/) account
- Create a LangSmith API key

<img width="600" alt="LangSmith Dashboard" src="https://github.com/user-attachments/assets/e39b8364-c3e3-4c75-a287-d9d4685caad5" />

<img width="600" alt="LangSmith API Keys" src="https://github.com/user-attachments/assets/2e916b2d-e3b0-4c59-a178-c5818604b8fe" />

- Update the .env file you created with your new LangSmith API Key.
- Check that `LANGSMITH_TRACING=true` is set in your .env file.

For more information on LangSmith, see our docs [here](https://docs.langchain.com/langsmith/home).

**Note:** If you enable LangSmith tracing by setting `LANGSMITH_TRACING=true` in your .env file, make sure you have a valid `LANGSMITH_API_KEY` set. The environment verification script (`env_utils.py`) will warn you if tracing is enabled without a valid key.

### Environment Variables

This course uses the [dotenv](https://pypi.org/project/python-dotenv) module to read key-value pairs from the .env file and set them in the environment in your scripts. They do not need to be set globally in your system environment.

**Note:** If you have API keys already set in your system environment, they may conflict with the ones in your .env file. The `env_utils.py` verification script will detect and warn you about such conflicts. By default, `load_dotenv()` does not override existing environment variables.

### Development Environment

This course uses Python scripts. You can edit and run them in any editor, including VSCode, Cursor, or Windsurf.
