"""数据分析智能体 — 负责 Text-to-SQL、数据查询和图表配置生成"""
import json
import re
from app.llm.client import llm_call
from app.llm.prompts import TEXT_TO_SQL_SYSTEM, CHART_CONFIG_SYSTEM
from app.tools.sql_executor import execute_sql


def _clean_sql(raw: str) -> str:
    """从 LLM 输出中提取纯 SQL"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:sql)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw.strip().rstrip(";") + ";"


def _safe_execute(sql: str, max_retries: int = 2) -> tuple[list[dict], str]:
    """执行 SQL，失败时让 LLM 修正"""
    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            results = execute_sql(sql)
            return results, sql
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                fix_prompt = f"这条SQL执行报错了:\n{sql}\n\n错误: {last_error}\n\n请修正SQL，只输出纯SQL语句。"
                fixed = llm_call(TEXT_TO_SQL_SYSTEM, fix_prompt, temperature=0.1, label="DataAnalyst-SQL修正")
                sql = _clean_sql(fixed)
    return [], sql


def data_analyst_node(state: dict) -> dict:
    """Text-to-SQL -> 执行查询 -> 生成图表配置"""
    user_query = state["user_query"]

    # Step 1: 生成 SQL
    raw_sql = llm_call(
        system_prompt=TEXT_TO_SQL_SYSTEM,
        user_prompt=user_query,
        temperature=0.1,
        label="DataAnalyst-Text2SQL",
    )
    sql = _clean_sql(raw_sql)

    # Step 2: 执行查询
    results, final_sql = _safe_execute(sql)

    # Step 3: 生成图表配置
    charts_config = None
    if results:
        try:
            chart_prompt = (
                f"用户问题: {user_query}\n"
                f"SQL查询: {final_sql}\n"
                f"查询结果（前20条）: {json.dumps(results[:20], ensure_ascii=False, default=str)}"
            )
            chart_raw = llm_call(
                system_prompt=CHART_CONFIG_SYSTEM,
                user_prompt=chart_prompt,
                temperature=0.3,
                label="DataAnalyst-图表生成",
            )
            chart_raw = chart_raw.strip()
            if chart_raw.startswith("```"):
                chart_raw = re.sub(r"^```(?:json)?\s*", "", chart_raw)
                chart_raw = re.sub(r"\s*```$", "", chart_raw)
            charts_config = json.loads(chart_raw)
        except (json.JSONDecodeError, Exception):
            charts_config = _fallback_chart(results, user_query)

    # 提取相关商品ID用于后续智能体
    product_ids = list({
        row.get("product_id") or row.get("id")
        for row in results
        if row.get("product_id") or row.get("id")
    })

    return {
        **state,
        "sql_query": final_sql,
        "query_result": results,
        "charts_config": charts_config,
        "related_product_ids": product_ids[:10],
        "agent_logs": state.get("agent_logs", []) + [
            {"agent": "data_analyst", "action": "text_to_sql", "sql": final_sql, "rows": len(results)}
        ],
    }


def _fallback_chart(results: list[dict], query: str) -> dict:
    """当 LLM 生成图表配置失败时的降级方案"""
    if not results:
        return None

    keys = list(results[0].keys())
    label_key = keys[0]
    value_keys = [k for k in keys[1:] if isinstance(results[0].get(k), (int, float))]

    if not value_keys:
        return None

    labels = [str(row.get(label_key, "")) for row in results[:10]]
    series = []
    for vk in value_keys[:3]:
        series.append({
            "name": vk,
            "type": "bar",
            "data": [row.get(vk, 0) for row in results[:10]],
        })

    return {
        "chart_type": "bar",
        "title": query[:30],
        "option": {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": [s["name"] for s in series]},
            "xAxis": {"type": "category", "data": labels, "axisLabel": {"rotate": 30}},
            "yAxis": {"type": "value"},
            "series": series,
        },
    }
