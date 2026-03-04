"""库存预警智能体 — 负责库存检查和补货建议"""
from app.tools.inventory_checker import get_alerts


def inventory_node(state: dict) -> dict:
    """检查相关商品库存并生成预警"""
    product_ids = state.get("related_product_ids", [])

    alerts = get_alerts(product_ids if product_ids else None)

    return {
        **state,
        "inventory_alerts": alerts,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "agent": "inventory",
                "action": "check",
                "urgent": alerts.get("urgent_count", 0),
                "warning": alerts.get("warning_count", 0),
            }
        ],
    }
