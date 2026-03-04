"""
生成具有代表性的服装电商模拟数据
- RBAC 用户/角色/权限
- 30+ 款商品，覆盖多品类/多区域
- 8000+ 条订单，跨越 6 个月
- 库存数据含预警场景
- 竞品数据含价格优劣势对比
"""
import random
from datetime import datetime, timedelta
import bcrypt
from app.database.connection import sync_engine, SyncSessionLocal
from app.database.models import (
    Base, Product, Order, Inventory, Competitor,
    Role, Permission, RolePermission, User,
    ChatSession, ChatMessage,
)

random.seed(42)


def _hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# ──────────────────────────────────────────────
# RBAC 初始数据
# ──────────────────────────────────────────────

ROLES = [
    ("admin",   "管理员",   "拥有全部权限，可管理用户和系统配置"),
    ("analyst", "分析师",   "可使用全部智能体查询与分析功能"),
    ("viewer",  "观察者",   "只读权限，可查看已有分析报告"),
]

PERMISSIONS = [
    ("chat:query",       "对话查询",   "使用智能体进行自然语言查询"),
    ("chat:export",      "导出数据",   "导出查询结果为 CSV/Excel"),
    ("feedback:submit",  "提交反馈",   "对 AI 回答进行赞/踩评价"),
    ("admin:user_manage","用户管理",   "新增/编辑/禁用系统用户"),
    ("admin:system",     "系统配置",   "修改系统配置与智能体参数"),
    ("data:view_report", "查看报告",   "查看历史分析报告"),
]

ROLE_PERMS = {
    "admin":   ["chat:query", "chat:export", "feedback:submit", "admin:user_manage", "admin:system", "data:view_report"],
    "analyst": ["chat:query", "chat:export", "feedback:submit", "data:view_report"],
    "viewer":  ["data:view_report"],
}

INIT_USERS = [
    ("admin",  "admin123",  "系统管理员",  "admin@datamind.com",  "admin"),
    ("analyst","analyst123","数据分析师",  "analyst@datamind.com","analyst"),
    ("demo",   "demo123",   "演示账号",    "demo@datamind.com",   "analyst"),
]

# ──────────────────────────────────────────────
# 电商数据
# ──────────────────────────────────────────────

PRODUCTS_DATA = [
    ("都市轻奢羊毛大衣", "外套", "大衣", "MODA", 899.0, 320.0, "华东", "爆款,冬季"),
    ("复古短款牛仔外套", "外套", "牛仔外套", "JEANS LAB", 359.0, 120.0, "华东", "新品,春季"),
    ("机能风冲锋衣Pro", "外套", "冲锋衣", "STORM", 599.0, 210.0, "华东", "爆款,户外"),
    ("法式小香风粗花呢外套", "外套", "小香风", "CHERIE", 769.0, 280.0, "华东", "爆款,新品"),
    ("男士商务羽绒服", "外套", "羽绒服", "NORTHMAX", 1299.0, 480.0, "华东", "冬季"),
    ("韩版oversize西装外套", "外套", "西装", "SEOULFIT", 459.0, 160.0, "华南", "春季"),
    ("户外三合一防风外套", "外套", "冲锋衣", "STORM", 699.0, 250.0, "华北", "户外"),
    ("少女甜酷皮衣", "外套", "皮衣", "REBEL", 529.0, 190.0, "华南", "新品"),
    ("纯棉基础圆领T恤3件装", "T恤", "基础款", "BASICGO", 129.0, 35.0, "华东", "爆款,基础"),
    ("重磅美式印花T恤", "T恤", "印花", "STREET90", 169.0, 55.0, "华北", "潮流"),
    ("冰丝凉感速干T恤", "T恤", "运动", "COOLMAX", 99.0, 30.0, "华南", "夏季,爆款"),
    ("设计师联名艺术T恤", "T恤", "联名", "ARTCO", 299.0, 90.0, "华东", "限量"),
    ("高腰直筒阔腿牛仔裤", "裤子", "牛仔裤", "JEANS LAB", 269.0, 85.0, "华东", "爆款"),
    ("弹力修身西装裤", "裤子", "西装裤", "SEOULFIT", 239.0, 75.0, "华南", "通勤"),
    ("户外速干工装裤", "裤子", "工装裤", "STORM", 329.0, 110.0, "华北", "户外"),
    ("女士加绒保暖打底裤", "裤子", "打底裤", "WARMFIT", 89.0, 25.0, "华东", "冬季,爆款"),
    ("碎花雪纺连衣裙", "连衣裙", "雪纺裙", "FLORA", 329.0, 100.0, "华南", "春季,新品"),
    ("法式方领泡泡袖连衣裙", "连衣裙", "法式", "CHERIE", 459.0, 150.0, "华东", "新品"),
    ("通勤气质衬衫裙", "连衣裙", "衬衫裙", "OFFICELADY", 389.0, 130.0, "华东", "通勤"),
    ("度假风吊带沙滩裙", "连衣裙", "沙滩裙", "FLORA", 259.0, 80.0, "华南", "夏季"),
    ("重磅纯棉连帽卫衣", "卫衣", "连帽", "STREET90", 249.0, 80.0, "华北", "潮流,爆款"),
    ("情侣款字母印花卫衣", "卫衣", "情侣款", "BASICGO", 199.0, 65.0, "华东", "新品"),
    ("宽松圆领落肩卫衣", "卫衣", "基础款", "BASICGO", 179.0, 55.0, "华南", "基础"),
    ("运动拉链立领卫衣", "卫衣", "运动", "COOLMAX", 219.0, 70.0, "华北", "运动"),
    ("民族风刺绣棉麻外套", "外套", "棉麻", "YUNSTYLE", 489.0, 170.0, "西南", "民族风"),
    ("轻薄防晒皮肤衣", "外套", "防晒", "COOLMAX", 159.0, 45.0, "华中", "夏季"),
    ("潮流拼接飞行员夹克", "外套", "飞行员", "REBEL", 429.0, 150.0, "华中", "潮流"),
    ("儿童可爱动物卫衣", "卫衣", "儿童", "KIDSFUN", 149.0, 45.0, "华东", "亲子"),
    ("男士纯色POLO衫", "T恤", "POLO", "BASICGO", 159.0, 50.0, "华南", "商务"),
    ("运动束脚休闲裤", "裤子", "运动裤", "COOLMAX", 189.0, 60.0, "华北", "运动"),
]

REGIONS = ["华东", "华南", "华北", "华中", "西南"]
CHANNELS = ["天猫", "京东", "抖音", "小红书", "线下"]
GENDERS = ["男", "女"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45+"]

REGION_WEIGHTS = {"华东": 0.35, "华南": 0.25, "华北": 0.20, "华中": 0.12, "西南": 0.08}
CHANNEL_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

MONTH_MULTIPLIER = {
    10: 0.9, 11: 1.3, 12: 1.5,
    1: 0.7, 2: 1.2, 3: 1.0,
}

CATEGORY_MONTH_BOOST = {
    "外套": {10: 1.2, 11: 1.8, 12: 2.0, 1: 1.5, 2: 1.6, 3: 0.8},
    "T恤":  {10: 0.6, 11: 0.5, 12: 0.3, 1: 0.3, 2: 0.4, 3: 1.0},
    "裤子": {10: 1.0, 11: 1.2, 12: 1.1, 1: 0.8, 2: 1.0, 3: 1.1},
    "连衣裙":{10: 0.5, 11: 0.4, 12: 0.3, 1: 0.3, 2: 0.5, 3: 1.2},
    "卫衣": {10: 1.3, 11: 1.5, 12: 1.4, 1: 1.2, 2: 1.3, 3: 1.0},
}

COMPETITORS_DATA = [
    (0, "都市轻奢羊毛大衣", "ZARA经典羊毛大衣", 1099.0, 3200, "天猫"),
    (0, "都市轻奢羊毛大衣", "优衣库羊毛混纺大衣", 799.0, 8500, "京东"),
    (0, "都市轻奢羊毛大衣", "H&M长款羊毛外套", 999.0, 2100, "天猫"),
    (2, "机能风冲锋衣Pro", "北面冲锋衣旗舰款", 1599.0, 5600, "天猫"),
    (2, "机能风冲锋衣Pro", "骆驼户外冲锋衣", 459.0, 12000, "京东"),
    (2, "机能风冲锋衣Pro", "迪卡侬防水冲锋衣", 399.0, 15000, "拼多多"),
    (3, "法式小香风粗花呢外套", "MANGO小香风外套", 899.0, 1800, "天猫"),
    (3, "法式小香风粗花呢外套", "太平鸟小香风套装", 689.0, 4200, "京东"),
    (4, "男士商务羽绒服", "波司登商务羽绒服", 1599.0, 9800, "天猫"),
    (4, "男士商务羽绒服", "雪中飞轻薄羽绒服", 699.0, 18000, "拼多多"),
    (8, "纯棉基础圆领T恤3件装", "优衣库U系列T恤3件", 149.0, 25000, "天猫"),
    (12, "高腰直筒阔腿牛仔裤", "UR高腰阔腿牛仔裤", 299.0, 6500, "天猫"),
    (12, "高腰直筒阔腿牛仔裤", "ONLY修身阔腿裤", 349.0, 4800, "京东"),
    (20, "重磅纯棉连帽卫衣", "Champion经典连帽卫衣", 399.0, 7200, "天猫"),
    (20, "重磅纯棉连帽卫衣", "李宁国潮连帽卫衣", 279.0, 11000, "京东"),
]


def _generate_orders(products: list[Product], start_date: datetime, end_date: datetime) -> list[dict]:
    orders = []
    current = start_date

    while current <= end_date:
        month = current.month
        base_multiplier = MONTH_MULTIPLIER.get(month, 1.0)

        for idx, p in enumerate(products):
            cat_boost = CATEGORY_MONTH_BOOST.get(p.category, {}).get(month, 1.0)
            weekday_boost = 1.1 if current.weekday() < 5 else 1.3
            daily_base = max(1, int(5 * base_multiplier * cat_boost * weekday_boost))

            if "爆款" in (p.tags or ""):
                daily_base = int(daily_base * 1.8)

            actual_count = random.randint(max(0, daily_base - 3), daily_base + 5)

            for _ in range(actual_count):
                region = p.region if random.random() < 0.5 else random.choices(
                    REGIONS, weights=[REGION_WEIGHTS[r] for r in REGIONS]
                )[0]
                channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
                gender = random.choice(GENDERS)
                age = random.choices(AGE_GROUPS, weights=[0.25, 0.40, 0.25, 0.10])[0]
                qty = random.choices([1, 2, 3], weights=[0.70, 0.22, 0.08])[0]
                discount = random.choice([1.0, 1.0, 1.0, 0.95, 0.90, 0.85, 0.80])
                unit_price = round(p.price * discount, 2)

                hour = random.choices(
                    range(24),
                    weights=[1,1,1,1,1,2,3,5,7,8,9,8,7,6,6,7,8,9,10,10,9,7,4,2]
                )[0]
                order_time = current.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))

                orders.append({
                    "product_id": idx + 1,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_amount": round(unit_price * qty, 2),
                    "region": region,
                    "channel": channel,
                    "customer_gender": gender,
                    "customer_age_group": age,
                    "order_date": order_time,
                })

        current += timedelta(days=1)

    return orders


def seed_database():
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)

    session = SyncSessionLocal()
    try:
        # ── RBAC ──
        role_objs = {}
        for name, display, desc in ROLES:
            r = Role(name=name, display_name=display, description=desc)
            session.add(r)
            role_objs[name] = r
        session.flush()

        perm_objs = {}
        for code, display, desc in PERMISSIONS:
            p = Permission(code=code, display_name=display, description=desc)
            session.add(p)
            perm_objs[code] = p
        session.flush()

        for role_name, perm_codes in ROLE_PERMS.items():
            for code in perm_codes:
                session.add(RolePermission(role_id=role_objs[role_name].id, permission_id=perm_objs[code].id))
        session.flush()

        for uname, pwd, dname, email, rname in INIT_USERS:
            session.add(User(
                username=uname,
                password_hash=_hash_pw(pwd),
                display_name=dname,
                email=email,
                role_id=role_objs[rname].id,
                is_active=True,
            ))
        session.flush()

        # ── 商品 ──
        products = []
        for name, cat, subcat, brand, price, cost, region, tags in PRODUCTS_DATA:
            p = Product(name=name, category=cat, subcategory=subcat, brand=brand,
                        price=price, cost=cost, region=region, tags=tags)
            session.add(p)
            products.append(p)
        session.flush()

        # ── 订单 ──
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2026, 3, 3)
        orders_data = _generate_orders(products, start_date, end_date)
        batch_size = 2000
        for i in range(0, len(orders_data), batch_size):
            session.execute(Order.__table__.insert(), orders_data[i:i + batch_size])
            session.flush()

        # ── 库存 ──
        warehouses = {"华东": "上海仓", "华南": "广州仓", "华北": "北京仓", "华中": "武汉仓", "西南": "成都仓"}
        for idx, p in enumerate(products):
            is_hot = "爆款" in (p.tags or "")
            stock = random.randint(5, 30) if is_hot else random.randint(80, 500)
            session.add(Inventory(
                product_id=idx + 1, stock_quantity=stock,
                warehouse=warehouses.get(p.region, "上海仓"),
                threshold=50 if is_hot else 30,
                last_restock_date=datetime.now() - timedelta(days=random.randint(5, 45)),
            ))

        # ── 竞品 ──
        for our_idx, pname, comp, cprice, csales, platform in COMPETITORS_DATA:
            session.add(Competitor(
                product_name=pname, our_product_id=our_idx + 1,
                competitor_name=comp, competitor_price=cprice,
                competitor_sales=csales, platform=platform,
                scraped_at=datetime.now() - timedelta(hours=random.randint(1, 72)),
            ))

        session.commit()
        print(f"数据生成完成: {len(ROLES)} 角色, {len(INIT_USERS)} 用户, {len(products)} 商品, {len(orders_data)} 订单")

    except Exception as e:
        session.rollback()
        print(f"数据生成失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import os, sys
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, backend_dir)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(backend_dir, ".env"))
    seed_database()
