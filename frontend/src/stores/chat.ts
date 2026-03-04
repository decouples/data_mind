import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatResponse, ExampleQuery, StreamStep, SessionSummary } from '../api/agent'
import {
  streamChat, getExamples, fetchSessions, fetchSessionMessages,
  saveMessage, deleteSessionApi,
} from '../api/agent'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  data?: Partial<ChatResponse>
  loading?: boolean
  stages?: StageInfo[]
  feedback?: number
}

export interface StageInfo {
  node: string
  message: string
  done: boolean
}

export interface SessionItem {
  id: string
  title: string
  updatedAt: number
  createdAt: number
  messageCount: number
  loaded: boolean
  messages: Message[]
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<SessionItem[]>([])
  const activeSessionId = ref('')
  const loading = ref(false)
  const examples = ref<ExampleQuery[]>([])
  const sessionsLoaded = ref(false)
  let abortController: AbortController | null = null

  const activeSession = computed(() => sessions.value.find(s => s.id === activeSessionId.value))
  const messages = computed(() => activeSession.value?.messages || [])

  // ── 从数据库加载会话列表（只有摘要） ──
  async function loadSessionList() {
    try {
      const list = await fetchSessions(100)
      const existing = new Map(sessions.value.map(s => [s.id, s]))
      const merged: SessionItem[] = list.map(s => {
        const prev = existing.get(s.id)
        return prev || _summaryToItem(s)
      })
      sessions.value = merged
      sessionsLoaded.value = true

      if (!activeSessionId.value || !sessions.value.find(s => s.id === activeSessionId.value)) {
        if (sessions.value.length > 0) {
          activeSessionId.value = sessions.value[0].id
        } else {
          _createEmptySession()
        }
      }
    } catch {
      sessionsLoaded.value = true
      if (sessions.value.length === 0) _createEmptySession()
    }
  }

  function _summaryToItem(s: SessionSummary): SessionItem {
    return {
      id: s.id, title: s.title,
      updatedAt: new Date(s.updated_at).getTime(),
      createdAt: new Date(s.created_at).getTime(),
      messageCount: s.message_count,
      loaded: false, messages: [],
    }
  }

  // ── 懒加载：点击会话时才拉取消息 ──
  async function switchSession(id: string) {
    const sess = sessions.value.find(s => s.id === id)
    if (!sess) return
    activeSessionId.value = id
    if (!sess.loaded && sess.messageCount > 0) {
      try {
        const detail = await fetchSessionMessages(id)
        sess.messages = detail.messages.map(m => ({
          id: m.id, role: m.role as Message['role'], content: m.content,
          timestamp: new Date(m.created_at).getTime(),
          data: m.data || undefined,
          feedback: m.feedback,
        }))
        sess.loaded = true
      } catch { /* keep empty */ }
    }
  }

  function newSession() {
    _createEmptySession()
  }

  function _createEmptySession() {
    const s: SessionItem = {
      id: generateId(), title: '新对话',
      updatedAt: Date.now(), createdAt: Date.now(),
      messageCount: 0, loaded: true, messages: [],
    }
    sessions.value.unshift(s)
    activeSessionId.value = s.id
  }

  async function deleteSession(id: string) {
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx === -1) return
    sessions.value.splice(idx, 1)
    deleteSessionApi(id).catch(() => {})
    if (activeSessionId.value === id) {
      if (sessions.value.length > 0) {
        activeSessionId.value = sessions.value[0].id
      } else {
        _createEmptySession()
      }
    }
  }

  function sendQuery(query: string) {
    const session = activeSession.value
    if (!session) return

    if (session.messages.length === 0) {
      session.title = query.length > 20 ? query.slice(0, 20) + '...' : query
    }

    const userMsg: Message = {
      id: generateId(), role: 'user', content: query, timestamp: Date.now(),
    }
    session.messages.push(userMsg)
    _persistMessage(session, userMsg)

    const aiMsgId = generateId()
    const aiMsg: Message = {
      id: aiMsgId, role: 'assistant', content: '', timestamp: Date.now(),
      loading: true, data: {},
      stages: [{ node: 'supervisor', message: '正在分析您的问题...', done: false }],
    }
    session.messages.push(aiMsg)

    loading.value = true

    abortController = streamChat(
      query,
      (step: StreamStep) => {
        const msg = session.messages.find(m => m.id === aiMsgId)
        if (!msg) return
        const existingStage = msg.stages?.find(s => s.node === step.node)
        if (existingStage) { existingStage.message = step.message; existingStage.done = true }
        else { msg.stages = msg.stages || []; msg.stages.push({ node: step.node, message: step.message, done: true }) }

        if (!msg.data) msg.data = {}
        if (step.intent) msg.data.intent = step.intent
        if (step.sql_query) msg.data.sql_query = step.sql_query
        if (step.query_result) msg.data.query_result = step.query_result
        if (step.charts_config) msg.data.charts_config = step.charts_config
        if (step.competitor_data) msg.data.competitor_data = step.competitor_data
        if (step.inventory_alerts) msg.data.inventory_alerts = step.inventory_alerts
        if (step.analysis_report) {
          msg.data.analysis_report = step.analysis_report
          msg.content = step.analysis_report
          msg.loading = false
          _persistMessage(session, msg)
        }
        if (step.error) {
          msg.data.error = step.error
          msg.content = `处理出错: ${step.error}`
          msg.loading = false
          _persistMessage(session, msg)
        }
        session.updatedAt = Date.now()
      },
      (doneData) => {
        const msg = session.messages.find(m => m.id === aiMsgId)
        if (msg) {
          msg.loading = false
          if (doneData.agent_logs && msg.data) msg.data.agent_logs = doneData.agent_logs
          _persistMessage(session, msg)
        }
        loading.value = false
        session.updatedAt = Date.now()
        abortController = null
      },
      (errMsg) => {
        const msg = session.messages.find(m => m.id === aiMsgId)
        if (msg) {
          msg.loading = false
          msg.content = `抱歉，处理时出现错误: ${errMsg}`
          _persistMessage(session, msg)
        }
        loading.value = false
        abortController = null
      },
    )
  }

  function _persistMessage(session: SessionItem, msg: Message) {
    saveMessage({
      session_id: session.id,
      session_title: session.title,
      message_id: msg.id,
      role: msg.role,
      content: msg.content,
      data: msg.data as Record<string, any> | undefined ?? null,
      feedback: msg.feedback ?? 0,
    }).catch(() => {})
  }

  function cancelQuery() {
    if (abortController) { abortController.abort(); abortController = null; loading.value = false }
  }

  async function loadExamples() {
    try { examples.value = await getExamples() } catch { examples.value = [] }
  }

  return {
    sessions, activeSessionId, activeSession, messages,
    loading, examples, sessionsLoaded,
    loadSessionList, switchSession, newSession, deleteSession,
    sendQuery, cancelQuery, loadExamples,
  }
})
