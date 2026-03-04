from pydantic import BaseModel
from typing import Any
from datetime import datetime


# ── 认证 ──

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str | None
    email: str | None
    role: str
    role_display: str
    permissions: list[str]


# ── 反馈 ──

class FeedbackRequest(BaseModel):
    session_id: str | None = None
    message_id: str
    query: str | None = None
    rating: int
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    message_id: str
    rating: int


# ── 会话历史 ──

class SessionSummary(BaseModel):
    """侧边栏列表用 — 只返回 id/title/time，不带消息体"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    data: dict[str, Any] | None = None
    feedback: int = 0
    created_at: datetime


class SessionDetail(BaseModel):
    id: str
    title: str
    messages: list[MessageOut]


class SaveMessageRequest(BaseModel):
    session_id: str
    session_title: str | None = None
    message_id: str
    role: str
    content: str = ""
    data: dict[str, Any] | None = None
    feedback: int = 0


# ── 对话 ──

class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None


class AgentLog(BaseModel):
    agent: str
    action: str
    result: str | None = None
    sql: str | None = None
    rows: int | None = None
    reason: str | None = None
    products: int | None = None
    urgent: int | None = None
    warning: int | None = None


class ChatResponse(BaseModel):
    query: str
    intent: str
    sql_query: str
    query_result: list[dict[str, Any]]
    charts_config: dict[str, Any] | None
    competitor_data: dict[str, Any] | None
    inventory_alerts: dict[str, Any] | None
    analysis_report: str
    agent_logs: list[dict[str, Any]]
    error: str


class HealthResponse(BaseModel):
    status: str
    message: str


class ExampleQuery(BaseModel):
    title: str
    query: str
    description: str
    category: str
