"""库存检查与预警工具"""
from app.tools.sql_executor import execute_sql


def check_inventory(product_ids: list[int] = None) -> list[dict]:
    """检查指定商品（或全部）的库存状态"""
    where = ""
    if product_ids:
        ids_str = ",".join(str(i) for i in product_ids)
        where = f"AND i.product_id IN ({ids_str})"

    sql = f"""
    SELECT
        p.id AS product_id,
        p.name AS product_name,
        p.category,
        i.stock_quantity,
        i.threshold,
        i.warehouse,
        i.last_restock_date,
        CASE
            WHEN i.stock_quantity <= i.threshold * 0.3 THEN '紧急'
            WHEN i.stock_quantity <= i.threshold THEN '预警'
            ELSE '正常'
        END AS stock_status,
        COALESCE(daily_avg.avg_daily_sales, 0) AS avg_daily_sales,
        CASE
            WHEN COALESCE(daily_avg.avg_daily_sales, 0) > 0
            THEN ROUND(i.stock_quantity / daily_avg.avg_daily_sales, 1)
            ELSE 999
        END AS days_of_stock
    FROM inventory i
    JOIN products p ON i.product_id = p.id
    LEFT JOIN (
        SELECT product_id, ROUND(AVG(daily_qty), 1) AS avg_daily_sales
        FROM (
            SELECT product_id, DATE(order_date) AS d, SUM(quantity) AS daily_qty
            FROM orders
            WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY product_id, DATE(order_date)
        ) t
        GROUP BY product_id
    ) daily_avg ON daily_avg.product_id = p.id
    WHERE 1=1 {where}
    ORDER BY
        CASE WHEN i.stock_quantity <= i.threshold * 0.3 THEN 0
             WHEN i.stock_quantity <= i.threshold THEN 1
             ELSE 2 END,
        days_of_stock ASC
    """
    return execute_sql(sql)


def get_alerts(product_ids: list[int] = None) -> dict:
    """生成库存预警报告"""
    inventory_data = check_inventory(product_ids)

    alerts = {
        "urgent": [],   # 紧急 (库存 < 30% 阈值)
        "warning": [],  # 预警 (库存 < 阈值)
        "normal": [],   # 正常
    }

    for item in inventory_data:
        status = item["stock_status"]
        record = {
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "category": item["category"],
            "stock": item["stock_quantity"],
            "threshold": item["threshold"],
            "warehouse": item["warehouse"],
            "avg_daily_sales": float(item["avg_daily_sales"]),
            "days_of_stock": float(item["days_of_stock"]),
            "restock_suggestion": "",
        }

        if status == "紧急":
            record["restock_suggestion"] = f"紧急补货！建议立即采购 {max(200, int(record['avg_daily_sales'] * 30))} 件"
            alerts["urgent"].append(record)
        elif status == "预警":
            record["restock_suggestion"] = f"建议补货 {max(100, int(record['avg_daily_sales'] * 21))} 件"
            alerts["warning"].append(record)
        else:
            alerts["normal"].append(record)

    return {
        "total_products": len(inventory_data),
        "urgent_count": len(alerts["urgent"]),
        "warning_count": len(alerts["warning"]),
        "alerts": alerts,
    }
