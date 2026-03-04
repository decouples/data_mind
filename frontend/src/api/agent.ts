import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('datamind_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('datamind_token')
      localStorage.removeItem('datamind_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export interface UserInfo {
  id: number
  username: string
  display_name: string | null
  email: string | null
  role: string
  role_display: string
  permissions: string[]
}

export interface LoginResult {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface ChatResponse {
  query: string
  intent: string
  sql_query: string
  query_result: Record<string, any>[]
  charts_config: Record<string, any> | null
  competitor_data: Record<string, any> | null
  inventory_alerts: Record<string, any> | null
  analysis_report: string
  agent_logs: Record<string, any>[]
  error: string
}

export interface ExampleQuery {
  title: string
  query: string
  description: string
  category: string
}

export interface StreamStep {
  node: string
  message: string
  intent?: string
  sql_query?: string
  query_result?: Record<string, any>[]
  charts_config?: Record<string, any> | null
  competitor_data?: Record<string, any> | null
  inventory_alerts?: Record<string, any> | null
  analysis_report?: string
  error?: string
}

export interface SessionSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface MessageOut {
  id: string
  role: string
  content: string
  data: Record<string, any> | null
  feedback: number
  created_at: string
}

export interface SessionDetail {
  id: string
  title: string
  messages: MessageOut[]
}

// ── Auth ──
export async function login(username: string, password: string): Promise<LoginResult> {
  const { data } = await api.post<LoginResult>('/auth/login', { username, password })
  return data
}
export async function getMe(): Promise<UserInfo> {
  const { data } = await api.get<UserInfo>('/auth/me')
  return data
}

// ── Sessions ──
export async function fetchSessions(limit = 100): Promise<SessionSummary[]> {
  const { data } = await api.get<SessionSummary[]>('/sessions', { params: { limit } })
  return data
}
export async function fetchSessionMessages(sessionId: string): Promise<SessionDetail> {
  const { data } = await api.get<SessionDetail>(`/sessions/${sessionId}`)
  return data
}
export async function saveMessage(payload: {
  session_id: string; session_title?: string; message_id: string;
  role: string; content?: string; data?: Record<string, any> | null; feedback?: number;
}) {
  await api.post('/sessions/message', payload)
}
export async function deleteSessionApi(sessionId: string) {
  await api.delete(`/sessions/${sessionId}`)
}

// ── Chat ──
export async function sendChat(query: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/chat', { query })
  return data
}
export async function getExamples(): Promise<ExampleQuery[]> {
  const { data } = await api.get<ExampleQuery[]>('/examples')
  return data
}

// ── Feedback ──
export async function submitFeedback(
  messageId: string, rating: number, sessionId?: string, query?: string, comment?: string,
) {
  const { data } = await api.post('/feedback', {
    message_id: messageId, rating, session_id: sessionId, query, comment,
  })
  return data
}

// ── Stream ──
export function streamChat(
  query: string,
  onStep: (step: StreamStep) => void,
  onDone: (data: { intent: string; agent_logs: Record<string, any>[] }) => void,
  onError: (err: string) => void,
): AbortController {
  const controller = new AbortController()
  const token = localStorage.getItem('datamind_token')

  fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ query }),
    signal: controller.signal,
  })
    .then((response) => {
      if (response.status === 401) {
        localStorage.removeItem('datamind_token')
        localStorage.removeItem('datamind_user')
        window.location.href = '/login'
        throw new Error('unauthorized')
      }
      if (!response.ok) throw new Error('请求失败')
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      function read(): Promise<void> {
        return reader.read().then(({ done, value }) => {
          if (done) return
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          let eventType = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) eventType = line.slice(7).trim()
            else if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (eventType === 'step') onStep(data as StreamStep)
                else if (eventType === 'status') onStep({ node: 'status', message: data.message, ...data })
                else if (eventType === 'done') onDone(data)
              } catch { /* skip */ }
            }
          }
          return read()
        })
      }
      return read()
    })
    .catch((err) => {
      if (err.name !== 'AbortError' && err.message !== 'unauthorized') onError(err.message)
    })

  return controller
}
