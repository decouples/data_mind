"""主调度智能体 — 负责意图识别、任务路由和结果汇总"""
import json
from app.llm.client import llm_call
from app.llm.prompts import INTENT_SYSTEM


def supervisor_node(state: dict) -> dict:
    """识别用户意图，决定调度哪些子智能体"""
    user_query = state["user_query"]

    intent = llm_call(
        system_prompt=INTENT_SYSTEM,
        user_prompt=user_query,
        temperature=0.1,
        label="Supervisor-意图识别",
    ).strip().lower()

    valid_intents = ["data_query", "data_analysis", "competitor_analysis", "inventory_check", "comprehensive"]
    if intent not in valid_intents:
        intent = "comprehensive"

    return {
        **state,
        "intent": intent,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "supervisor", "action": "intent_recognition", "result": intent}
        ],
    }


def report_generator_node(state: dict) -> dict:
    """汇总所有智能体结果，生成最终报告"""
    from app.llm.prompts import ANALYSIS_SYSTEM

    context_parts = []

    if state.get("query_result"):
        context_parts.append(f"【数据查询结果】\n{json.dumps(state['query_result'], ensure_ascii=False, indent=2, default=str)}")

    if state.get("competitor_data") and state["competitor_data"].get("status") == "ok":
        context_parts.append(f"【竞品分析数据】\n{json.dumps(state['competitor_data']['data'], ensure_ascii=False, indent=2, default=str)}")

    if state.get("inventory_alerts"):
        alerts = state["inventory_alerts"]
        context_parts.append(f"【库存预警信息】\n紧急: {alerts.get('urgent_count', 0)}件, 预警: {alerts.get('warning_count', 0)}件\n{json.dumps(alerts.get('alerts', {}), ensure_ascii=False, indent=2, default=str)}")

    if not context_parts:
        return {**state, "analysis_report": "抱歉，未能获取到相关数据。请尝试换一种方式提问。"}

    context = "\n\n".join(context_parts)
    user_prompt = f"用户问题: {state['user_query']}\n\n以下是收集到的数据:\n{context}"

    report = llm_call(
        system_prompt=ANALYSIS_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.7,
        label="Reporter-报告生成",
    )

    return {
        **state,
        "analysis_report": report,
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "reporter", "action": "generate_report", "result": "done"}
        ],
    }
