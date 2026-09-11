# OfficeFlow Customer Support Agent (Emma)

Bienvenido a la implementación de **OfficeFlow Agent**, el agente conversacional protagonista del curso **Building Reliable Agents** de LangChain Academy.

Emma es una especialista en soporte al cliente para **OfficeFlow Supply Co.**, una empresa distribuidora de suministros de oficina y papelería para empresas en Norteamérica. A lo largo del curso, Emma evoluciona desde un prototipo rudimentario (v0) hasta un agente robusto, optimizado y listo para producción (v5).

---

## 🗺️ Mapa de Versiones y Evolución del Agente

| Versión | Archivo Script | Documentación | Característica Clave Introducida | Problema que Resuelve |
| :--- | :--- | :--- | :--- | :--- |
| **v0** | [`agent_v0.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v0.py) | [`agent_v0.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v0.md) | Agente base con OpenAI Tools sin observabilidad. | Punto de partida; imposible saber qué hace internamente sin logs manuales. |
| **v1** | [`agent_v1.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v1.py) | [`agent_v1.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v1.md) | Instrumentación completa con **LangSmith Tracing**. | Permite inspeccionar en UI cada llamada a LLM, argumentos de herramientas, latencia y tokens. |
| **v2** | [`agent_v2.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v2.py) | [`agent_v2.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v2.md) | Descubrimiento de esquema en la herramienta SQL (`PRAGMA table_info`). | Evita que el agente adivine nombres de tablas/columnas e invente SQL erróneo. |
| **v3** | [`agent_v3.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v3.py) | [`agent_v3.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v3.md) | Política de revelación de stock (**Stock Policy**). | Protege la ventaja competitiva no revelando cantidades exactas (usa adjetivos como "pocas unidades"). |
| **v4** | [`agent_v4.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v4.py) | [`agent_v4.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v4.md) | **No-Chunking RAG** (documentos completos en lugar de fragmentos). | Elimina la pérdida de contexto de fragmentos (ej: plazos de devolución o excepciones de envío). |
| **v5** | [`agent_v5.py`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v5.py) | [`agent_v5.md`](file:///f:/Cursos_code/LANGCHAIN/Building_Releable_Agents/officeflow-agent/agent_v5.md) | Prioridad de concisión (**Conciseness Priority**). | Reduce el texto superfluo, acelera la respuesta al usuario y disminuye costes de generación. |

---

## 🗄️ Estructura de Recursos del Agente

- **`inventory/`**:
  - `inventory.db`: Base de datos relacional SQLite con el catálogo de productos, precios, categorías y existencias.
- **`knowledge_base/`**:
  - `documents/`: Archivos Markdown de políticas de empresa (`company_info.md`, `ordering_policy.md`, `returns_policy.md`, `shipping_policy.md`, `locations_contact.md`).
  - `embeddings/embeddings.json`: Embeddings precalculados con OpenAI `text-embedding-3-small`.
  - `generate_embeddings.py`: Script para recalcular embeddings cuando los documentos cambian.
