"""LangGraph 多智能体编排 — 定义状态图和条件路由"""
import time
import logging
from typing import TypedDict, Generator
from langgraph.graph import StateGraph, END

from app.agents.supervisor import supervisor_node, report_generator_node
from app.agents.data_analyst import data_analyst_node
from app.agents.competitor import competitor_node
from app.agents.inventory import inventory_node

logger = logging.getLogger("graph")


class AgentState(TypedDict, total=False):
    user_query: str
    intent: str
    sql_query: str
    query_result: list
    charts_config: dict | None
    related_product_ids: list
    competitor_data: dict
    inventory_alerts: dict
    analysis_report: str
    agent_logs: list
    error: str


def route_by_intent(state: dict) -> str:
    intent = state.get("intent", "comprehensive")
    route_map = {
        "data_query": "data_analyst",
        "data_analysis": "data_analyst",
        "competitor_analysis": "data_analyst",
        "inventory_check": "inventory",
        "comprehensive": "data_analyst",
    }
    return route_map.get(intent, "data_analyst")


def after_data_analyst(state: dict) -> str:
    intent = state.get("intent", "")
    if intent in ("comprehensive", "competitor_analysis"):
        return "competitor"
    elif intent == "inventory_check":
        return "inventory"
    return "reporter"


def after_competitor(state: dict) -> str:
    if state.get("intent", "") == "comprehensive":
        return "inventory"
    return "reporter"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("data_analyst", data_analyst_node)
    graph.add_node("competitor", competitor_node)
    graph.add_node("inventory", inventory_node)
    graph.add_node("reporter", report_generator_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges("supervisor", route_by_intent, {
        "data_analyst": "data_analyst",
        "inventory": "inventory",
    })

    graph.add_conditional_edges("data_analyst", after_data_analyst, {
        "competitor": "competitor",
        "inventory": "inventory",
        "reporter": "reporter",
    })

    graph.add_conditional_edges("competitor", after_competitor, {
        "inventory": "inventory",
        "reporter": "reporter",
    })

    graph.add_edge("inventory", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


agent_graph = build_graph()


def run_agent(user_query: str) -> dict:
    """同步运行完整图，返回最终状态"""
    initial_state = _make_initial_state(user_query)
    try:
        return agent_graph.invoke(initial_state)
    except Exception as e:
        return {**initial_state, "error": str(e), "analysis_report": f"处理过程中出现错误: {str(e)}"}


def run_agent_stepwise(user_query: str) -> Generator[tuple[str, dict], None, None]:
    """逐步执行 agent 图，每完成一个节点就 yield (node_name, partial_state)。

    这样 SSE 端点可以在每一步完成后立刻推送中间结果给前端。
    """
    state = _make_initial_state(user_query)

    intent = state.get("intent", "comprehensive")

    # Step 1: Supervisor
    try:
        state = supervisor_node(state)
        intent = state.get("intent", "comprehensive")
        yield ("supervisor", state)
    except Exception as e:
        state["error"] = str(e)
        yield ("error", state)
        return

    # Step 2: 按意图决定路径
    route = route_by_intent(state)

    if route == "inventory":
        # inventory_check 意图：直接走 inventory -> reporter
        try:
            state = inventory_node(state)
            yield ("inventory", state)
        except Exception as e:
            state["error"] = str(e)
            yield ("error", state)

        try:
            state = report_generator_node(state)
            yield ("reporter", state)
        except Exception as e:
            state["error"] = str(e)
            yield ("error", state)
        return

    # Step 3: DataAnalyst
    try:
        state = data_analyst_node(state)
        yield ("data_analyst", state)
    except Exception as e:
        state["error"] = str(e)
        yield ("error", state)

    # Step 4: 是否需要 competitor
    next_step = after_data_analyst(state)
    if next_step == "competitor":
        try:
            state = competitor_node(state)
            yield ("competitor", state)
        except Exception as e:
            state["error"] = str(e)
            yield ("error", state)

        # comprehensive 还需要 inventory
        if after_competitor(state) == "inventory":
            try:
                state = inventory_node(state)
                yield ("inventory", state)
            except Exception as e:
                state["error"] = str(e)
                yield ("error", state)

    elif next_step == "inventory":
        try:
            state = inventory_node(state)
            yield ("inventory", state)
        except Exception as e:
            state["error"] = str(e)
            yield ("error", state)

    # Step last: Reporter
    try:
        state = report_generator_node(state)
        yield ("reporter", state)
    except Exception as e:
        state["error"] = str(e)
        yield ("error", state)


def _make_initial_state(user_query: str) -> dict:
    return {
        "user_query": user_query,
        "intent": "",
        "sql_query": "",
        "query_result": [],
        "charts_config": None,
        "related_product_ids": [],
        "competitor_data": {},
        "inventory_alerts": {},
        "analysis_report": "",
        "agent_logs": [],
        "error": "",
    }
