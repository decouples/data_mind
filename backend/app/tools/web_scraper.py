"""竞品数据获取工具

实际生产中会爬取真实电商平台，这里从数据库 competitors 表中查询模拟数据，
并包装成「爬取结果」的格式返回。
"""
from app.tools.sql_executor import execute_sql


def scrape_competitor_prices(product_ids: list[int] = None, product_names: list[str] = None) -> list[dict]:
    """根据商品ID或名称查询竞品价格数据"""
    conditions = []
    if product_ids:
        ids_str = ",".join(str(i) for i in product_ids)
        conditions.append(f"c.our_product_id IN ({ids_str})")
    if product_names:
        names_str = ",".join(f"'{n}'" for n in product_names)
        conditions.append(f"c.product_name IN ({names_str})")

    where = " OR ".join(conditions) if conditions else "1=1"

    sql = f"""
    SELECT
        c.product_name AS our_product,
        p.price AS our_price,
        c.competitor_name,
        c.competitor_price,
        c.competitor_sales AS estimated_monthly_sales,
        c.platform,
        ROUND((p.price - c.competitor_price) / c.competitor_price * 100, 1) AS price_diff_pct,
        c.scraped_at
    FROM competitors c
    JOIN products p ON c.our_product_id = p.id
    WHERE {where}
    ORDER BY c.product_name, c.competitor_price
    """
    return execute_sql(sql)


def get_competitor_summary(product_ids: list[int]) -> dict:
    """生成竞品分析摘要"""
    data = scrape_competitor_prices(product_ids=product_ids)
    if not data:
        return {"status": "no_data", "message": "未找到相关竞品数据"}

    summary = {}
    for row in data:
        product = row["our_product"]
        if product not in summary:
            summary[product] = {
                "our_price": row["our_price"],
                "competitors": [],
                "avg_competitor_price": 0,
                "price_position": "",
            }
        summary[product]["competitors"].append({
            "name": row["competitor_name"],
            "price": row["competitor_price"],
            "sales": row["estimated_monthly_sales"],
            "platform": row["platform"],
            "diff_pct": row["price_diff_pct"],
        })

    for product, info in summary.items():
        avg_price = sum(c["price"] for c in info["competitors"]) / len(info["competitors"])
        info["avg_competitor_price"] = round(avg_price, 2)
        if info["our_price"] < avg_price * 0.9:
            info["price_position"] = "价格优势明显"
        elif info["our_price"] > avg_price * 1.1:
            info["price_position"] = "价格偏高"
        else:
            info["price_position"] = "价格适中"

    return {"status": "ok", "data": summary}
