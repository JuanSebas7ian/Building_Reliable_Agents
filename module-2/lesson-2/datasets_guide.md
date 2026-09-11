# Módulo 2 - Lección 2: Creación y Gestión de Datasets (`officeflow-dataset.csv`)

## 🎯 Propósito y Concepto Teórico
Para evaluar de manera científica y reproducible un agente de IA, no basta con interactuar manualmente en un chat. Es indispensable contar con un **Dataset de Evaluación** (*Golden Dataset*) que represente la distribución real de consultas que el agente enfrentará en producción.

En LangSmith, un Dataset es una colección de ejemplos compuestos por:
- **Inputs**: Los datos de entrada que recibirá el agente (por ejemplo, la pregunta del usuario `question`).
- **Outputs (Opcional)**: Respuestas de referencia o criterios esperados (*ground truth*).
- **Metadata (Opcional)**: Etiquetas como categoría de la consulta, dificultad, etc.

---

## 📁 El Archivo `officeflow-dataset.csv`

El archivo [`officeflow-dataset.csv`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/officeflow-dataset.csv) contiene 25 preguntas cuidadosamente diseñadas para poner a prueba los puntos críticos del agente Emma:

1. **Preguntas de Existencias y Stock (Prueba de la Política de Stock)**:
   - *"How many reams of copy paper do you currently have available?"*
   - *"We go through a LOT of pens. I need to know exactly how many blue ballpoint pen packs are in your warehouse before I commit to ordering."*
2. **Preguntas de Catálogo e Inventario (Prueba de Herramientas SQL)**:
   - *"Do you carry ballpoint pens?"*
   - *"Can you check if you have spiral notebooks AND staplers in stock?"*
3. **Preguntas Fuera de Catálogo (Prueba de No Alucinación)**:
   - *"I'm looking for pet food for my cats, do you carry Purina?"*
4. **Preguntas de Políticas Corporativas (Prueba de RAG)**:
   - *"What is your return policy? How long do I have to return something?"*
   - *"How much does shipping cost and how long does it take to get my order?"*
5. **Casos Límite y Frustración del Cliente (Prueba de Tono y Empatía)**:
   - *"I'm very unhappy with the stapler I received. It only staples 3 sheets before it jams!"*
   - *"This is the THIRD time I've called about my lost package. Tracking says delivered but I never got it."*

---

## 📤 Cómo Cargar el Dataset en LangSmith

Para poder ejecutar los experimentos de las lecciones 3, 4, 5 y 6, debes cargar este dataset en tu cuenta de LangSmith con el nombre exacto `officeflow-dataset`:

### Opción 1: Desde la Interfaz Web de LangSmith (Recomendado)
1. Inicia sesión en [https://smith.langchain.com/](https://smith.langchain.com/).
2. En el menú lateral izquierdo, haz clic en **Datasets & Testing**.
3. Haz clic en el botón superior derecho **+ New Dataset**.
4. Nómbralo: `officeflow-dataset`.
5. Selecciona el tipo: **Key-Value**.
6. Haz clic en **Upload CSV** y selecciona el archivo [`module-2/lesson-2/officeflow-dataset.csv`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/module-2/lesson-2/officeflow-dataset.csv).
7. Mapea la columna `question` como **Input**.
8. Haz clic en **Create**.

### Opción 2: Mediante Código Python con el SDK de LangSmith
```python
from langsmith import Client
import pandas as pd

client = Client()
df = pd.read_csv("officeflow-dataset.csv")

dataset = client.create_dataset(
    dataset_name="officeflow-dataset",
    description="Preguntas de prueba para evaluar al agente de soporte Emma de OfficeFlow"
)

for _, row in df.iterrows():
    client.create_example(
        inputs={"question": row["question"]},
        outputs={},
        dataset_id=dataset.id
    )
```
