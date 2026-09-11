# Módulo 3 - Lección 2: `upload_traces.py` (Ingesta Masiva de Trazas a LangSmith)

## 🎯 Propósito y Concepto Teórico
Este script toma el archivo de trazas sintéticas `synthetic_traces.json` y las sube en masa a un proyecto de **LangSmith** utilizando la clase de bajo nivel `RunTree`.

Además, implementa un mecanismo crítico: **desplazamiento temporal dinámico (Time Shifting)**. Dado que las trazas estáticas guardadas en un JSON tendrían fechas del pasado, el script calcula la diferencia entre la fecha actual y la fecha de la última traza, proyectando todas las trazas hacia el momento presente para que aparezcan en los paneles de telemetría y filtros temporales de hoy en LangSmith.

---

## 🛠️ Arquitectura del Script

1. **Cálculo del Desplazamiento Temporal**:
   ```python
   latest = max(parse_dt(r["start_time"]) for r in runs if r["start_time"])
   time_delta = datetime.now(timezone.utc).replace(tzinfo=None) - latest
   ```

2. **Regeneración de Identificadores Únicos (`uuid7`)**:
   - Para evitar colisiones de IDs entre diferentes estudiantes o ejecuciones repetidas, se mapea cada ID antiguo a un nuevo `UUIDv7` fresco.

3. **Reconstrucción del Árbol Jerárquico con `RunTree`**:
   - Se procesan primero los nodos raíz (sin `parent_run_id`).
   - Se vinculan los hijos mediante `root_tree.create_child()`.
   - Se finalizan con sus tiempos y outputs correspondientes (`tree.end()`).
   - Se envían a la API con `root_tree.post(exclude_child_runs=False)`.

4. **Vaciado de Cola (`client.flush()`)**:
   - Asegura que todas las peticiones asíncronas en segundo plano hayan sido confirmadas por los servidores de LangSmith antes de finalizar el proceso.

---

## 🚀 Cómo Ejecutar

Desde la carpeta `module-3/lesson-2/`:

```bash
cd module-3/lesson-2
python upload_traces.py --project lca-reliable-agents
```

Opcionalmente, puedes especificar un proyecto destino diferente pasando `--project nombre-de-proyecto`.
Al finalizar, abre tu proyecto en LangSmith para explorar cientos de trazas agregadas y analizarlas con filtros avanzados y herramientas de monitoreo.
