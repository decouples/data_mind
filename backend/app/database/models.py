from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Text, Index, Boolean, SmallInteger,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ──────────────────────────────────────────────
# RBAC 权限模型
# ──────────────────────────────────────────────

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色名: admin/analyst/viewer")
    display_name = Column(String(100), comment="角色显示名称，如 管理员/分析师/观察者")
    description = Column(String(255), comment="角色描述，用于说明该角色具有哪些能力")
    created_at = Column(DateTime, default=datetime.now)

    users = relationship("User", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, comment="权限编码: chat:query / admin:user_manage / data:export 等")
    display_name = Column(String(100), comment="权限显示名称")
    description = Column(String(255), comment="权限说明，便于管理员理解各权限含义")
    created_at = Column(DateTime, default=datetime.now)

    roles = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    """角色-权限关联表，实现多对多"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

    __table_args__ = (
        Index("idx_role_perm_unique", "role_id", "permission_id", unique=True),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="登录用户名，唯一")
    password_hash = Column(String(255), nullable=False, comment="bcrypt 哈希后的密码")
    display_name = Column(String(100), comment="前端显示昵称")
    email = Column(String(200), comment="邮箱，可选，用于通知")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="所属角色ID")
    is_active = Column(Boolean, default=True, comment="是否启用，False表示已禁用")
    last_login_at = Column(DateTime, comment="最近一次登录时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    role = relationship("Role", back_populates="users")
    feedbacks = relationship("Feedback", back_populates="user")

    __table_args__ = (
        Index("idx_user_role", "role_id"),
    )


# ──────────────────────────────────────────────
# 对话历史
# ──────────────────────────────────────────────

class ChatSession(Base):
    """每次「新建对话」产生一条记录"""
    __tablename__ = "chat_sessions"

    id = Column(String(100), primary_key=True, comment="前端生成的会话ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户，用于隔离")
    title = Column(String(200), default="新对话", comment="会话标题，取自第一条用户提问")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan",
                            order_by="ChatMessage.created_at")

    __table_args__ = (
        Index("idx_chat_session_user", "user_id"),
        Index("idx_chat_session_updated", "updated_at"),
    )


class ChatMessage(Base):
    """单条消息（用户或AI回复），JSON存完整数据"""
    __tablename__ = "chat_messages"

    id = Column(String(100), primary_key=True, comment="前端生成的消息ID")
    session_id = Column(String(100), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, comment="user / assistant")
    content = Column(Text, default="", comment="文本内容（报告正文）")
    data_json = Column(Text, comment="AI回复的结构化数据（charts/competitor/inventory等），JSON格式")
    feedback = Column(SmallInteger, default=0, comment="0=未评价 1=赞 -1=踩")
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("idx_chat_msg_session", "session_id"),
    )


# ──────────────────────────────────────────────
# 反馈 (赞/踩)
# ──────────────────────────────────────────────

class Feedback(Base):
    """用户对每条AI回答的赞踩记录，用于后期复盘模型效果"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="操作用户")
    session_id = Column(String(100), comment="前端会话ID，用于关联完整对话上下文")
    message_id = Column(String(100), nullable=False, comment="前端消息ID，标识是哪条回答")
    query = Column(Text, comment="用户原始提问，便于回溯")
    rating = Column(SmallInteger, nullable=False, comment="1=赞 -1=踩")
    comment = Column(Text, comment="用户可选填的补充评价")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="feedbacks")

    __table_args__ = (
        Index("idx_feedback_user", "user_id"),
        Index("idx_feedback_message", "message_id"),
    )


# ──────────────────────────────────────────────
# 电商业务表
# ──────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="商品名称")
    category = Column(String(50), nullable=False, comment="品类: 外套/T恤/裤子/连衣裙/卫衣")
    subcategory = Column(String(50), comment="子品类: 风衣/羽绒服/牛仔外套等")
    brand = Column(String(100), comment="品牌")
    price = Column(Float, nullable=False, comment="售价")
    cost = Column(Float, comment="成本价")
    region = Column(String(50), nullable=False, comment="销售区域: 华东/华南/华北/华中/西南")
    tags = Column(String(200), comment="标签: 爆款/新品/清仓等")
    created_at = Column(DateTime, default=datetime.now)

    orders = relationship("Order", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", uselist=False)

    __table_args__ = (
        Index("idx_product_category_region", "category", "region"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, comment="购买数量")
    unit_price = Column(Float, nullable=False, comment="成交单价")
    total_amount = Column(Float, nullable=False, comment="订单金额")
    region = Column(String(50), nullable=False, comment="下单区域")
    channel = Column(String(50), comment="渠道: 天猫/京东/抖音/小红书/线下")
    customer_gender = Column(String(10), comment="客户性别")
    customer_age_group = Column(String(20), comment="年龄段: 18-24/25-34/35-44/45+")
    order_date = Column(DateTime, nullable=False, comment="下单时间")
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="orders")

    __table_args__ = (
        Index("idx_order_date_region", "order_date", "region"),
        Index("idx_order_product", "product_id"),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    stock_quantity = Column(Integer, nullable=False, comment="当前库存")
    warehouse = Column(String(100), comment="仓库: 上海仓/广州仓/北京仓/武汉仓/成都仓")
    threshold = Column(Integer, default=50, comment="预警阈值")
    last_restock_date = Column(DateTime, comment="上次补货日期")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    product = relationship("Product", back_populates="inventory")


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(200), nullable=False, comment="对标商品名")
    our_product_id = Column(Integer, ForeignKey("products.id"), comment="我方对应商品ID")
    competitor_name = Column(String(100), nullable=False, comment="竞品品牌/店铺")
    competitor_price = Column(Float, nullable=False, comment="竞品价格")
    competitor_sales = Column(Integer, comment="竞品月销量估算")
    platform = Column(String(50), comment="平台: 天猫/京东/拼多多")
    scraped_at = Column(DateTime, default=datetime.now)
    notes = Column(Text, comment="备注")
