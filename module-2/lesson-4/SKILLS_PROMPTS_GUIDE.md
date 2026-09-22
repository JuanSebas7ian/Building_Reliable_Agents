# Catálogo de Prompts y Guía de Uso de Skills (Lección 4)

> **Ubicación**: [`module-2/lesson-4/SKILLS_PROMPTS_GUIDE.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/SKILLS_PROMPTS_GUIDE.md)  
> **Skills Asociados**: [`langsmith-evaluator`](file:///f:/Cursos_code/LANGCHAIN/.agents/skills/langsmith-evaluator/SKILL.md) & [`langsmith-trace`](file:///f:/Cursos_code/LANGCHAIN/.agents/skills/langsmith-trace/SKILL.md)  
> **Objetivo**: Proporcionar el catálogo exacto de instrucciones (prompts) en lenguaje natural para interactuar con Antigravity y construir la suite de evaluación determinista de la Lección 4.

---

## 🧭 ¿Cómo funcionan estos Prompts con los Skills?

Cuando instalamos los skills oficiales de LangSmith en `.agents/skills/`, Antigravity adquiere un marco de referencia especializado. En lugar de tener que explicarle manualmente la API o la firma de funciones de LangSmith, simplemente mencionas el nombre del skill en tu instrucción (prompt) y el modelo sabrá qué estándares técnicos aplicar.

---

## 📋 Catálogo de Prompts de la Lección 4

---

### 🔹 Prompt 1 - Evaluador de Trayectoria SQL (schema_before_query)

**Texto exacto del prompt:**

> *"Usa el skill **langsmith-evaluator** para crear un evaluador determinista de trayectoria en Python llamado `schema_before_query`. Debe inspeccionar la lista de `tool_calls` del run y validar que si el agente usó `query_database`, la primera llamada haya sido una consulta de esquema (`PRAGMA table_info` o `sqlite_master`) antes de cualquier `SELECT` de datos. Debe devolver score 1 si cumple o no aplica, y score 0 si intentó adivinar tablas a ciegas."*

**Explicación técnica detallada:**

- **Problema que resuelve:** Los agentes que interactúan con SQL frecuentemente "alucinan" nombres de tablas o columnas inexistentes (ej. inventan una columna `price` o una tabla `products`).
- **Qué construye el Skill:** Una función offline `schema_before_query(run, example=None) -> dict` que:
  1. Extrae los mensajes y sus `tool_calls` tanto de objetos `RunTree` como de diccionarios.
  2. Filtra únicamente las llamadas a `query_database`.
  3. Comprueba cronológicamente si apareció una sentencia de inspección (`PRAGMA table_info`, `sqlite_master`, `.schema`) antes del primer `SELECT` de datos.
  4. Retorna `{"key": "schema_before_query", "score": 1, "comment": "..."}` si cumplió, o `score: 0` con la consulta infractora.
- **Archivo generado:** [`eval_schema_check.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_schema_check.py)

---

### 🔹 Prompt 2 - Evaluador de Política de Confidencialidad de Stock (check_no_exact_quantities)

**Texto exacto del prompt:**

> *"Usa el skill **langsmith-evaluator** para crear un evaluador basado en código llamado `check_no_exact_quantities`. Debe aplicar expresiones regulares sobre el texto de respuesta del agente para detectar si expuso números exactos de existencias (ej. 'we have 45 pens', '12 units left'). Debe retornar `{'score': 1, 'comment': '...'}` si utilizó bandas cualitativas permitidas ('in stock', 'running low'), o `{'score': 0, ...}` si filtró el número confidencial."*

**Explicación técnica detallada:**

- **Problema que resuelve:** Por políticas de negocio de OfficeFlow, revelar el número exacto de inventario está prohibido. El agente debe usar bandas cualitativas (*in stock*, *running low*, *almost sold out*).
- **Qué construye el Skill:** Una función determinista en Python con expresiones regulares (`re`) optimizadas:
  1. Detecta patrones numéricos ligados a productos de almacén (`we have \d+ units`, `in stock: \d+`, `exactly \d+`).
  2. Si encuentra coincidencias, penaliza con `score: 0` y lista los fragmentos infractores.
  3. Si la respuesta utiliza bandas cualitativas autorizadas, premia con `score: 1`.
- **Archivo generado:** [`eval_stock_policy.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/eval_stock_policy.py)

---

### 🔹 Prompt 3 - Wrapper de Aislamiento de Sesión (Run Function)

**Texto exacto del prompt:**

> *"Siguiendo las directrices del skill **langsmith-evaluator**, diseña la función `run_agent(inputs)` para Emma. Asegúrate de: (1) generar un `thread_id` UUIDv7 fresco por cada fila del dataset para evitar contaminación de memoria, y (2) estructurar el retorno para que incluya tanto el texto final como la lista completa de `messages` con sus `tool_calls` para que los evaluadores de trayectoria puedan inspeccionarlos."*

**Explicación técnica detallada:**

- **Problema que resuelve:** En un agente con memoria conversacional, si la pregunta 1 fue sobre papel y la pregunta 2 es sobre engrapadoras, el historial previo puede sesgar las respuestas posteriores (*Memory Leak / Contaminación*).
- **Qué construye el Skill:** La función objetivo que recibe las entradas del dataset (`inputs={"question": "..."}`), aísla la sesión con `agent_v5.thread_id = str(uuid7())` y empaqueta la salida en una estructura que contiene `output`, `messages` y el conteo de tokens.
- **Archivo generado:** Integrado dentro de [`run_eval.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/run_eval.py).

---

### 🔹 Prompt 4 - Orquestación del Experimento Completo

**Texto exacto del prompt:**

> *"Usa el skill **langsmith-evaluator** para orquestar la ejecución de `evaluate()` contra el dataset 'officeflow-dataset' usando los evaluadores `schema_before_query` y `check_no_exact_quantities`. El experimento debe tener como prefijo 'code-eval-v5' y cargar la base de conocimiento vectorial antes de iniciar."*

**Explicación técnica detallada:**

- **Problema que resuelve:** Automatiza la ejecución secuencial o paralela de las 25 preguntas del dataset contra Emma y calcula las métricas globales para publicarlas en la nube de LangSmith.
- **Qué construye el Skill:** El bloque principal `evaluate()` que descarga el dataset de LangSmith, ejecuta `run_agent`, pasa la salida a los dos evaluadores y genera la URL interactiva.
- **Archivo generado:** [`run_eval.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/run_eval.py)

---

### 🔹 Prompt 5 - Auditoría y Diagnóstico de Trazas (langsmith-trace)

**Texto exacto del prompt:**

> *"Usa el skill **langsmith-trace** para buscar en nuestro proyecto de LangSmith todas las ejecuciones donde el evaluador `stock_policy_compliance` o `schema_before_query` haya dado una puntuación de 0, y muéstrame el query o la respuesta exacta que causó la infracción."*

**Explicación técnica detallada:**

- **Problema que resuelve:** Cuando un experimento tiene fallos (puntuaciones 0), buscar manualmente entre 25 o 100 preguntas en la interfaz web es tedioso.
- **Qué hace el Skill:** Se conecta mediante `Client()` a la API de LangSmith, filtra por el ID del experimento y por el feedback score `< 1`, extrayendo únicamente los casos defectuosos con sus comentarios de diagnóstico.

---

## ⚡ 3. Resumen de Ejecución Rápida

| Objetivo | Comando CMD | Comando PowerShell |
| :--- | :--- | :--- |
| **Probar Evaluador SQL** | `uv run python eval_schema_check.py` | `uv run python eval_schema_check.py` |
| **Probar Evaluador Stock** | `uv run python eval_stock_policy.py` | `uv run python eval_stock_policy.py` |
| **Lanzar Experimento Completo** | `uv run python run_eval.py` | `uv run python run_eval.py` |
