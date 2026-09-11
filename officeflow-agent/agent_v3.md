# Agente OfficeFlow: `agent_v3.py` (+ Política de Información de Stock)

## 🎯 Propósito y Contexto
Al evaluar `agent_v2.py` frente al documento de requisitos del producto (**PRD - Product Requirements Document**) de OfficeFlow, se detecta una violación grave de la política comercial de la empresa:
> **Requisito del PRD**: *"Para proteger nuestra ventaja competitiva y estrategia de inventario frente a competidores, el agente NUNCA debe divulgar cantidades numéricas exactas de stock a los clientes."*

En `agent_v2.py`, el agente respondía: *"Tenemos 15 paquetes de cuadernos en el almacén"*. 
`agent_v3.py` introduce en el `system_prompt` una política explícita de bandas cualitativas de inventario.

---

## 🔄 Cambios Respecto a `agent_v2.py`

### Inclusión de la Política de Stock en el System Prompt

```markdown
IMPORTANT - STOCK INFORMATION POLICY:
When discussing product availability, NEVER reveal specific stock quantities or numbers to customers. Instead:
- If quantity > 20: Say the item is "in stock" or "available"
- If quantity 10-20: Say the item is "in stock, but running low" or "available, though inventory is limited" to create urgency
- If quantity 5-9: Say "only a few left in stock" or "limited availability" to encourage quick action
- If quantity 1-4: Say "very limited stock remaining" or "almost sold out"
- If quantity 0: Say "currently out of stock" or "unavailable at the moment"

This policy protects our competitive advantage and inventory management strategy while still helping customers make informed purchasing decisions.
```

---

## 🧪 Comparativa de Respuestas

| Pregunta del Usuario | Respuesta en `agent_v2` (Fallo de PRD) | Respuesta en `agent_v3` (Conforme a PRD) |
| :--- | :--- | :--- |
| *"¿Cuántos paquetes de papel tienen en existencia?"* | *"Tenemos 34 resmas de papel en el almacén."* | *"Tenemos papel disponible y en stock para entrega inmediata."* |
| *"¿Tienen cuadernos de espiral?"* (Stock = 12) | *"Nos quedan exactamente 12 unidades."* | *"Sí, tenemos cuadernos disponibles, aunque nuestro inventario es limitado en este momento."* |

---

## 🚀 Cómo Ejecutar

```bash
cd officeflow-agent
python agent_v3.py
```
