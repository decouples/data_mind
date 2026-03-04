"""竞品分析智能体 — 负责竞品价格对比和市场定位分析"""
import json
from app.tools.web_scraper import get_competitor_summary
from app.llm.client import llm_call


def competitor_node(state: dict) -> dict:
    """获取竞品数据并分析"""
    product_ids = state.get("related_product_ids", [])

    if not product_ids:
        return {
            **state,
            "competitor_data": {"status": "no_data", "message": "无相关商品ID，跳过竞品分析"},
            "agent_logs": state.get("agent_logs", []) + [
                {"agent": "competitor", "action": "skipped", "reason": "no product_ids"}
            ],
        }

    # 调用竞品爬虫工具
    competitor_data = get_competitor_summary(product_ids)

    # 如果有数据，生成简要竞品分析
    if competitor_data.get("status") == "ok" and competitor_data.get("data"):
        analysis_prompt = (
            f"以下是我方商品与竞品的价格对比数据，请简要分析竞争态势:\n"
            f"{json.dumps(competitor_data['data'], ensure_ascii=False, indent=2, default=str)}"
        )
        competitor_insight = llm_call(
            system_prompt="你是竞品分析专家，简明扼要地分析价格竞争力和市场定位。用3-5个要点总结。",
            user_prompt=analysis_prompt,
            temperature=0.5,
            label="Competitor-竞品分析",
        )
        competitor_data["insight"] = competitor_insight

    return {
        **state,
        "competitor_data": competitor_data,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "competitor", "action": "analyze", "products": len(product_ids)}
        ],
    }
