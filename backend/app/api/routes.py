import json
import time
import queue
import asyncio
import logging
import threading
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session as SaSession

from app.schemas.response import (
    ChatRequest, ChatResponse, HealthResponse, ExampleQuery,
    LoginRequest, LoginResponse, UserInfo,
    FeedbackRequest, FeedbackResponse,
    SessionSummary, SessionDetail, MessageOut, SaveMessageRequest,
)
from app.agents.graph import run_agent, run_agent_stepwise
from app.auth import (
    verify_password, create_access_token, get_current_user, _get_db,
)
from app.database.models import User, Feedback, ChatSession, ChatMessage

logger = logging.getLogger("api")

router = APIRouter()

_SENTINEL = object()

EXAMPLE_QUERIES = [
    ExampleQuery(title="华东区外套销售TOP5", query="帮我看看上个月华东区哪几款外套卖得最好，并分析原因",
                 description="综合分析：数据查询 + 竞品对比 + 库存检查", category="comprehensive"),
    ExampleQuery(title="各渠道销售占比", query="分析一下最近三个月各渠道（天猫、京东、抖音等）的销售额占比和趋势变化",
                 description="数据分析：多维度聚合 + 趋势图表", category="data_analysis"),
    ExampleQuery(title="爆款商品竞品对比", query="把我们的爆款商品和竞品的价格对比一下，看看我们的竞争力如何",
                 description="竞品分析：价格对比 + 市场定位", category="competitor_analysis"),
    ExampleQuery(title="库存预警检查", query="检查一下当前库存情况，哪些商品需要紧急补货？",
                 description="库存预警：阈值检测 + 补货建议", category="inventory_check"),
    ExampleQuery(title="25-34岁客群分析", query="分析25-34岁客户群体最喜欢买什么品类，客单价是多少",
                 description="数据查询：人群画像 + 消费偏好", category="data_analysis"),
    ExampleQuery(title="双12大促效果复盘", query="帮我复盘去年12月的销售数据，和11月对比看看增长情况",
                 description="数据分析：同比环比 + 大促效果评估", category="data_analysis"),
]


# ──────────────────────────────────────────────
# 认证
# ──────────────────────────────────────────────

@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: Annotated[SaSession, Depends(_get_db)]):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    user.last_login_at = datetime.now()
    db.commit()
    role = user.role
    perms = [rp.permission.code for rp in role.permissions]
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(access_token=token, user=UserInfo(
        id=user.id, username=user.username, display_name=user.display_name,
        email=user.email, role=role.name, role_display=role.display_name, permissions=perms,
    ))


@router.get("/auth/me", response_model=UserInfo)
async def get_me(user: Annotated[User, Depends(get_current_user)]):
    role = user.role
    perms = [rp.permission.code for rp in role.permissions]
    return UserInfo(
        id=user.id, username=user.username, display_name=user.display_name,
        email=user.email, role=role.name, role_display=role.display_name, permissions=perms,
    )


# ──────────────────────────────────────────────
# 会话历史
# ──────────────────────────────────────────────

@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[SaSession, Depends(_get_db)],
    limit: int = Query(100, ge=1, le=500),
):
    """返回当前用户的会话列表（只含摘要），按更新时间倒序，上限 limit 条"""
    rows = (
        db.query(
            ChatSession.id,
            ChatSession.title,
            ChatSession.created_at,
            ChatSession.updated_at,
            func.count(ChatMessage.id).label("message_count"),
        )
        .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.user_id == user.id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        SessionSummary(id=r.id, title=r.title, created_at=r.created_at,
                       updated_at=r.updated_at, message_count=r.message_count)
        for r in rows
    ]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_messages(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[SaSession, Depends(_get_db)],
):
    """懒加载：点击某个会话时才获取其全部消息"""
    sess = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user.id,
    ).first()
    if not sess:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = [
        MessageOut(
            id=m.id, role=m.role, content=m.content,
            data=json.loads(m.data_json) if m.data_json else None,
            feedback=m.feedback or 0, created_at=m.created_at,
        )
        for m in sess.messages
    ]
    return SessionDetail(id=sess.id, title=sess.title, messages=msgs)


@router.post("/sessions/message")
async def save_message(
    req: SaveMessageRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[SaSession, Depends(_get_db)],
):
    """前端每产生一条消息就调用此接口持久化"""
    sess = db.query(ChatSession).filter(
        ChatSession.id == req.session_id, ChatSession.user_id == user.id,
    ).first()
    if not sess:
        sess = ChatSession(id=req.session_id, user_id=user.id,
                           title=req.session_title or "新对话")
        db.add(sess)
        db.flush()
    elif req.session_title:
        sess.title = req.session_title

    existing = db.query(ChatMessage).filter(ChatMessage.id == req.message_id).first()
    if existing:
        existing.content = req.content
        existing.data_json = json.dumps(req.data, ensure_ascii=False, default=str) if req.data else None
        existing.feedback = req.feedback
    else:
        db.add(ChatMessage(
            id=req.message_id, session_id=req.session_id, role=req.role,
            content=req.content,
            data_json=json.dumps(req.data, ensure_ascii=False, default=str) if req.data else None,
            feedback=req.feedback,
        ))

    sess.updated_at = datetime.now()
    db.commit()
    return {"ok": True}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[SaSession, Depends(_get_db)],
):
    sess = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user.id,
    ).first()
    if sess:
        db.delete(sess)
        db.commit()
    return {"ok": True}


# ──────────────────────────────────────────────
# 反馈
# ──────────────────────────────────────────────

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    req: FeedbackRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[SaSession, Depends(_get_db)],
):
    if req.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="rating 只能为 1(赞) 或 -1(踩)")

    existing = db.query(Feedback).filter(
        Feedback.user_id == user.id, Feedback.message_id == req.message_id,
    ).first()
    if existing:
        existing.rating = req.rating
        existing.comment = req.comment
        db.commit()
        return FeedbackResponse(id=existing.id, message_id=existing.message_id, rating=existing.rating)

    fb = Feedback(user_id=user.id, session_id=req.session_id, message_id=req.message_id,
                  query=req.query, rating=req.rating, comment=req.comment)
    db.add(fb)
    db.commit()
    db.refresh(fb)

    msg = db.query(ChatMessage).filter(ChatMessage.id == req.message_id).first()
    if msg:
        msg.feedback = req.rating
        db.commit()

    return FeedbackResponse(id=fb.id, message_id=fb.message_id, rating=fb.rating)


# ──────────────────────────────────────────────
# 公共
# ──────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", message="电商数据智能体服务运行中")


@router.get("/examples", response_model=list[ExampleQuery])
async def get_examples():
    return EXAMPLE_QUERIES


# ──────────────────────────────────────────────
# 对话 (需登录)
# ──────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: Annotated[User, Depends(get_current_user)]):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    logger.info(f"[{user.username}] 收到查询: {request.query}")
    start = time.time()
    result = await asyncio.to_thread(run_agent, request.query)
    elapsed = time.time() - start
    logger.info(f"[{user.username}] 查询完成 | 耗时: {elapsed:.1f}s | 意图: {result.get('intent')}")
    return ChatResponse(
        query=request.query, intent=result.get("intent", ""), sql_query=result.get("sql_query", ""),
        query_result=result.get("query_result", []), charts_config=result.get("charts_config"),
        competitor_data=result.get("competitor_data"), inventory_alerts=result.get("inventory_alerts"),
        analysis_report=result.get("analysis_report", ""), agent_logs=result.get("agent_logs", []),
        error=result.get("error", ""),
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, user: Annotated[User, Depends(get_current_user)]):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    logger.info(f"[stream][{user.username}] 收到查询: {request.query}")

    async def event_generator():
        yield _sse("status", {"stage": "supervisor", "message": "正在分析您的问题..."})
        start = time.time()
        q: queue.Queue = queue.Queue()

        def _produce():
            try:
                for node_name, state in run_agent_stepwise(request.query):
                    q.put((node_name, state))
            except Exception as e:
                q.put(("error", {"error": str(e)}))
            finally:
                q.put(_SENTINEL)

        thread = threading.Thread(target=_produce, daemon=True)
        thread.start()

        last_state = {}
        while True:
            try:
                item = await asyncio.to_thread(q.get, timeout=300)
            except Exception:
                break
            if item is _SENTINEL:
                break
            node_name, state = item
            last_state = state
            yield _build_step_sse(node_name, state)

        elapsed = time.time() - start
        logger.info(f"[stream][{user.username}] 查询完成 | 耗时: {elapsed:.1f}s")
        yield _sse("done", {"intent": last_state.get("intent", ""), "agent_logs": last_state.get("agent_logs", [])})

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


def _build_step_sse(node_name: str, state: dict) -> str:
    if node_name == "supervisor":
        return _sse("step", {"node": "supervisor", "intent": state.get("intent", ""),
                             "message": f"意图识别完成: {state.get('intent', '')}"})
    elif node_name == "data_analyst":
        return _sse("step", {"node": "data_analyst", "sql_query": state.get("sql_query", ""),
                             "query_result": state.get("query_result", []),
                             "charts_config": state.get("charts_config"),
                             "message": f"数据查询完成，获取到 {len(state.get('query_result', []))} 条记录"})
    elif node_name == "competitor":
        return _sse("step", {"node": "competitor", "competitor_data": state.get("competitor_data"),
                             "message": "竞品分析完成"})
    elif node_name == "inventory":
        alerts = state.get("inventory_alerts", {})
        return _sse("step", {"node": "inventory", "inventory_alerts": alerts,
                             "message": f"库存检查完成，发现 {alerts.get('urgent_count', 0)} 个紧急预警"})
    elif node_name == "reporter":
        return _sse("step", {"node": "reporter", "analysis_report": state.get("analysis_report", ""),
                             "message": "分析报告生成完成"})
    else:
        return _sse("step", {"node": "error", "error": state.get("error", "未知错误"),
                             "message": f"处理出错: {state.get('error', '')}"})


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
