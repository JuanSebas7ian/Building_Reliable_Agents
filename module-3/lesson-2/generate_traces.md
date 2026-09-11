# Módulo 3 - Lección 2: `generate_traces.py` (Generador de Trazas Sintéticas a Escala)

## 🎯 Propósito y Concepto Teórico
En entornos de producción, analizar trazas una a una resulta inviable. Cuando un agente recibe miles de consultas al día, los ingenieros de IA necesitan **técnicas de análisis a escala** (clustering de consultas, detección automática de fallos, embudos de latencia y costes).

Para estudiar este escenario sin necesidad de desplegar el agente a miles de usuarios reales, este script genera un conjunto masivo de trazas sintéticas realistas que simulan semanas de tráfico de producción de OfficeFlow, guardadas en el archivo `synthetic_traces.json`.

---

## ⚙️ Componentes de la Simulación

1. **Variabilidad de Consultas**:
   - Preguntas sencillas de una sola llamada.
   - Consultas complejas que requieren múltiples llamadas a herramientas y reintentos.
   - Preguntas que generan errores de base de datos o excepciones en tiempo de ejecución.
2. **Distribución de Tiempos y Latencias**:
   - Distribución log-normal simulando latencias reales de red y procesamiento de LLMs.
3. **Estructura Jerárquica Completa**:
   - Cada traza incluye nodos raíz (`chain`), llamadas a LLM (`llm`) y llamadas a herramientas (`tool`) con timestamps y cálculo de tokens reales.

---

## 🚀 Cómo Ejecutar (Opcional)

Si deseas regenerar el archivo `synthetic_traces.json`:

```bash
cd module-3/lesson-2
python generate_traces.py
```
*(El archivo precalculado ya viene incluido en el repositorio).*
