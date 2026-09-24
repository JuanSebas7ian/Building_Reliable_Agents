# Catálogo y Guía Oficial de Agent Skills para MLflow

> **Repositorio Oficial**: [`github.com/mlflow/skills`](https://github.com/mlflow/skills) en [skills.sh](https://skills.sh/mlflow/skills)  
> **Ubicación en el Proyecto**: [`module-2/lesson-4/MLFLOW_SKILLS_CATALOG.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-4/MLFLOW_SKILLS_CATALOG.md)  
> **Propósito**: Guía completa de los 13 Agent Skills oficiales de MLflow para evaluación, observabilidad (tracing), depuración y optimización de agentes LLM en Antigravity.

---

## 🧭 1. ¿Qué son los MLflow Skills?

Al igual que LangChain mantiene `langsmith-skills`, el equipo de **MLflow / Databricks** desarrolló un ecosistema de **Agent Skills** modulares diseñados para dotar a los asistentes de programación con IA (como Antigravity) de capacidades especializadas para:

- Evaluar agentes de forma sistemática con datasets y scorers.
- Instrumentar observabilidad en tiempo real (*MLflow Tracing*).
- Depurar alucinaciones y malas elecciones de herramientas analizando trazas.
- Buscar documentación oficial y métricas agregadas de costos/tokens.

---

## 📊 2. Tabla Comparativa: LangSmith Skills vs. MLflow Skills

| Área de Trabajo | Skill Oficial en LangSmith | Skill Oficial en MLflow (`mlflow/skills`) |
| :--- | :--- | :--- |
| **Evaluación de Agentes con Datasets** | `langsmith-evaluator` | **`agent-evaluation`** |
| **Construcción de Rúbricas y Jueces** | `langsmith-evaluator` | **`build-a-scorer`** |
| **Instrumentación de Tracing** | `langsmith-trace` | **`instrumenting-with-mlflow-tracing`** |
| **Búsqueda y Filtrado de Trazas** | `langsmith-trace` | **`retrieving-mlflow-traces`** |
| **Auditoría y Análisis de 1 Traza** | `langsmith-trace` | **`analyzing-mlflow-trace`** |
| **Análisis de Sesiones Multi-Turno** | — | **`analyzing-mlflow-session`** |
| **Diagnóstico de Causa Raíz** | — | **`debug-agent`** |
| **Corrección de Alucinaciones / Errores** | — | **`fix-agent-issue`** |
| **Métricas Agregadas (Costos y Tokens)** | — | **`querying-mlflow-metrics`** |
| **Búsqueda de Documentación Oficial** | — | **`searching-mlflow-docs`** |
| **Orquestador Principal** | — | **`mlflow-agent`** |
| **Integración Cloud AWS** | — | **`sagemaker-mlflow`** |
| **Onboarding / Primeros Pasos** | — | **`mlflow-onboarding`** |

---

## 🛠️ 3. Desglose Detallado de los 13 Skills de MLflow

---

### 1. `agent-evaluation` (Evaluador de Agentes)

- **Cuándo usarlo:** Cuando necesites evaluar, mejorar u optimizar sistemáticamente la calidad de respuesta de un agente LLM, la precisión en la selección de herramientas, o reducir costos.
- **Qué cubre:** El flujo completo de evaluación de MLflow con datasets, definición de scorers deterministas y LLM judges, y ejecución de `mlflow.evaluate()`.

---

### 2. `build-a-scorer` (Diseñador de Jueces y Métricas)

- **Cuándo usarlo:** Cuando quieras pasar de cero a un prototipo de evaluación funcional. Ayuda a definir criterios de calidad atómicos y a implementar cada criterio con el scorer más económico y confiable (código determinista vs. LLM-as-a-judge).

---

### 3. `instrumenting-with-mlflow-tracing` (Instrumentación de Trazabilidad)

- **Cuándo usarlo:** Al agregar observabilidad a aplicaciones en Python o TypeScript. Soporta LangGraph, LangChain, OpenAI nativo, Gemini, DSPy, CrewAI y AutoGen.

---

### 4. `retrieving-mlflow-traces` (Recuperación de Trazas)

- **Cuándo usarlo:** Para consultar la API de MLflow o el CLI buscando trazas por ID, estado (exitoso/fallido), etiquetas, metadatos o latencia (`traces slower than X seconds`).

---

### 5. `analyzing-mlflow-trace` (Análisis de Traza Individual)

- **Cuándo usarlo:** Cuando tengas el ID de una traza fallida y necesites entender la causa raíz del error o la secuencia de tool calls que provocó la falla.

---

### 6. `analyzing-mlflow-session` (Análisis de Conversación Multi-Turno)

- **Cuándo usarlo:** Para depurar sesiones completas de chat donde un cliente tuvo una mala experiencia a lo largo de varios turnos conversacionales.

---

### 7. `debug-agent` (Diagnóstico sin Cambios de Código)

- **Cuándo usarlo:** Para explicar por qué el agente produjo cierta salida basándose en la evidencia de la traza, sin apresurarse a tocar el prompt.

---

### 8. `fix-agent-issue` (Ciclo de Corrección de Comportamiento)

- **Cuándo usarlo:** Guía el ciclo disciplinado: *Explorar traza → Planificar → Implementar → Verificar con tests de regresión en `@mlflow.test`*. Evita parches rápidos en el prompt cuando el error real está en una herramienta o en la recuperación RAG.

---

### 9. `querying-mlflow-metrics` (Analítica de Rendimiento)

- **Cuándo usarlo:** Para generar reportes de consumo de tokens, costos acumulados de llamadas a LLM y tendencias de latencia desde el Tracking Server.

---

### 10. `searching-mlflow-docs` (Buscador de Documentación)

- **Cuándo usarlo:** Para consultar en tiempo real guías y referencias de API de MLflow sin salir del entorno de desarrollo.

---

### 11. `mlflow-agent` (Despachador Maestro)

- **Cuándo usarlo:** Punto de entrada cuando tienes una tarea general de MLflow y quieres que el sistema delegue automáticamente al sub-skill correcto.

---

### 12. `mlflow-onboarding` (Guía de Inicio)

- **Cuándo usarlo:** Para configurar el tracking server inicial y enlazar experimentos nuevos.

---

### 13. `sagemaker-mlflow` (Conexión AWS)

- **Cuándo usarlo:** Para conectar Antigravity a servidores administrados de MLflow en AWS SageMaker.

---

## 💻 4. Comandos de Instalación para Antigravity

Puedes instalar los skills en tu workspace con `npx skills`:

### Opción A: Los 2 Skills Esenciales (Evaluación + Tracing)

Recomendado si quieres replicar exactamente lo que hicimos en la Lección 4:

```powershell
npx skills add mlflow/skills --skill agent-evaluation instrumenting-with-mlflow-tracing --yes
```

### Opción B: El Paquete Completo (Los 13 Skills)

Para tener la suite completa de desarrollo, evaluación y depuración de MLflow:

```powershell
npx skills add mlflow/skills --skill '*' --yes
```

---

## 💬 5. Ejemplos de Prompts para Invocar estos Skills

Una vez instalados, puedes interactuar con Antigravity en lenguaje natural:

1. **Para evaluar un agente con MLflow:**
   > *"Usa el skill **agent-evaluation** para configurar una prueba de estrés del agente Emma contra nuestro dataset de 25 preguntas usando `mlflow.evaluate()`."*

2. **Para crear un evaluador:**
   > *"Usa el skill **build-a-scorer** para diseñar un scorer de MLflow que penalice al agente si revela stock numérico confidencial."*

3. **Para instrumentar trazabilidad:**
   > *"Usa el skill **instrumenting-with-mlflow-tracing** para envolver las llamadas de OpenAI de Emma y registrar cada consulta a SQLite como un span hijo."*

4. **Para depurar un fallo:**
   > *"Usa el skill **analyzing-mlflow-trace** para examinar la traza con ID `tr-abc123` y decirme por qué el agente no usó la base de conocimiento."*
