from sqlalchemy import text
from app.database.connection import sync_engine


def execute_sql(sql: str) -> list[dict]:
    """执行 SQL 查询并返回结果列表"""
    with sync_engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = []
        for row in result.fetchall():
            rows.append(dict(zip(columns, row)))
        return rows


def get_table_schema() -> str:
    """返回数据库表结构摘要，用于 LLM 上下文"""
    schema_sql = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    rows = execute_sql(schema_sql)
    schema_text = ""
    current_table = ""
    for row in rows:
        if row["TABLE_NAME"] != current_table:
            current_table = row["TABLE_NAME"]
            schema_text += f"\n表 {current_table}:\n"
        comment = row.get("COLUMN_COMMENT", "")
        schema_text += f"  - {row['COLUMN_NAME']}: {row['DATA_TYPE']}"
        if comment:
            schema_text += f" ({comment})"
        schema_text += "\n"
    return schema_text
