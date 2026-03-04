<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore, type SessionItem } from '../stores/chat'
import { useAuthStore } from '../stores/auth'
import MessageBubble from '../components/MessageBubble.vue'
import ChatInput from '../components/ChatInput.vue'
import WelcomePanel from '../components/WelcomePanel.vue'
import DetailPanel from '../components/DetailPanel.vue'

const chatStore = useChatStore()
const authStore = useAuthStore()
const router = useRouter()
const messagesContainer = ref<HTMLElement>()
const showDetail = ref(false)
const selectedMessage = ref<any>(null)
const olderExpanded = ref(false)

const hasMessages = computed(() => chatStore.messages.length > 0)

interface GroupedSessions { today: SessionItem[]; week: SessionItem[]; older: SessionItem[] }

const grouped = computed<GroupedSessions>(() => {
  const now = Date.now()
  const todayStart = new Date(); todayStart.setHours(0, 0, 0, 0)
  const weekAgo = todayStart.getTime() - 6 * 86400000

  const g: GroupedSessions = { today: [], week: [], older: [] }
  for (const s of chatStore.sessions) {
    const t = s.updatedAt
    if (t >= todayStart.getTime()) g.today.push(s)
    else if (t >= weekAgo) g.week.push(s)
    else g.older.push(s)
  }
  return g
})

const olderVisible = computed(() => olderExpanded.value ? grouped.value.older : grouped.value.older.slice(0, 3))

onMounted(async () => {
  chatStore.loadExamples()
  await chatStore.loadSessionList()
  if (chatStore.activeSessionId && chatStore.activeSession && !chatStore.activeSession.loaded) {
    await chatStore.switchSession(chatStore.activeSessionId)
  }
})

watch(() => chatStore.messages.length, async () => { await nextTick(); scrollToBottom() })
watch(() => chatStore.messages.map(m => m.content).join(''), async () => { await nextTick(); scrollToBottom() })

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({ top: messagesContainer.value.scrollHeight, behavior: 'smooth' })
  }
}

function handleSend(query: string) { chatStore.sendQuery(query) }
function handleExampleClick(query: string) { chatStore.sendQuery(query) }
function handleViewDetail(msg: any) { selectedMessage.value = msg; showDetail.value = true }
function handleCloseDetail() { showDetail.value = false }
function handleLogout() { authStore.logout(); router.push('/login') }

async function handleSwitchSession(id: string) {
  await chatStore.switchSession(id)
}

function formatTime(ts: number): string {
  const d = new Date(ts)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="chat-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              <polyline points="7.5 4.21 12 6.81 16.5 4.21"/><line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>
          </div>
          <div class="logo-text"><h1>DataMind</h1><span>电商数据智能体</span></div>
        </div>
      </div>

      <div class="sidebar-content">
        <button class="new-chat-btn" @click="chatStore.newSession()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          新建对话
        </button>

        <!-- History groups -->
        <div class="sidebar-section history-section">
          <template v-if="grouped.today.length">
            <h3>今天</h3>
            <div class="history-list">
              <div v-for="s in grouped.today" :key="s.id" class="history-item"
                   :class="{ active: s.id === chatStore.activeSessionId }"
                   @click="handleSwitchSession(s.id)">
                <div class="history-info">
                  <span class="history-title">{{ s.title }}</span>
                  <span class="history-time">{{ formatTime(s.updatedAt) }}</span>
                </div>
                <button class="history-delete" @click.stop="chatStore.deleteSession(s.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </template>

          <template v-if="grouped.week.length">
            <h3>最近7天</h3>
            <div class="history-list">
              <div v-for="s in grouped.week" :key="s.id" class="history-item"
                   :class="{ active: s.id === chatStore.activeSessionId }"
                   @click="handleSwitchSession(s.id)">
                <div class="history-info">
                  <span class="history-title">{{ s.title }}</span>
                  <span class="history-time">{{ formatTime(s.updatedAt) }}</span>
                </div>
                <button class="history-delete" @click.stop="chatStore.deleteSession(s.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>
          </template>

          <template v-if="grouped.older.length">
            <h3>更早</h3>
            <div class="history-list">
              <div v-for="s in olderVisible" :key="s.id" class="history-item"
                   :class="{ active: s.id === chatStore.activeSessionId }"
                   @click="handleSwitchSession(s.id)">
                <div class="history-info">
                  <span class="history-title">{{ s.title }}</span>
                  <span class="history-time">{{ formatTime(s.updatedAt) }}</span>
                </div>
                <button class="history-delete" @click.stop="chatStore.deleteSession(s.id)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
              <button v-if="grouped.older.length > 3" class="expand-btn" @click="olderExpanded = !olderExpanded">
                {{ olderExpanded ? '收起' : `展开更多 (${grouped.older.length - 3})` }}
              </button>
            </div>
          </template>

          <div v-if="!chatStore.sessions.length" class="no-history">暂无对话记录</div>
        </div>

        <div class="sidebar-section">
          <h3>智能体状态</h3>
          <div class="agent-status-list">
            <div class="agent-status-item"><span class="status-dot active"></span><span class="agent-name">主调度智能体</span></div>
            <div class="agent-status-item"><span class="status-dot active"></span><span class="agent-name">数据分析智能体</span></div>
            <div class="agent-status-item"><span class="status-dot active"></span><span class="agent-name">竞品分析智能体</span></div>
            <div class="agent-status-item"><span class="status-dot active"></span><span class="agent-name">库存预警智能体</span></div>
          </div>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div class="user-detail">
            <span class="user-name">{{ authStore.displayName }}</span>
            <span class="user-role">{{ authStore.roleName }}</span>
          </div>
          <button class="logout-btn" title="退出登录" @click="handleLogout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div class="chat-container">
        <div class="chat-area">
          <div v-if="!hasMessages" class="welcome-wrapper">
            <WelcomePanel :examples="chatStore.examples" @select="handleExampleClick" />
          </div>
          <div v-else ref="messagesContainer" class="messages-container">
            <TransitionGroup name="message">
              <MessageBubble v-for="msg in chatStore.messages" :key="msg.id" :message="msg" @view-detail="handleViewDetail" />
            </TransitionGroup>
          </div>
          <div class="input-area">
            <ChatInput :loading="chatStore.loading" @send="handleSend" />
          </div>
        </div>
        <Transition name="slide-panel">
          <DetailPanel v-if="showDetail && selectedMessage?.data" :data="selectedMessage.data" @close="handleCloseDetail" />
        </Transition>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-layout { display: flex; height: 100vh; overflow: hidden; }

.sidebar {
  width: 280px; min-width: 280px;
  background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
  color: white; display: flex; flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}
.sidebar-header { padding: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.logo { display: flex; align-items: center; gap: 12px; }
.logo-icon { width: 40px; height: 40px; background: rgba(255, 255, 255, 0.15); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #a5b4fc; }
.logo-text h1 { font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em; }
.logo-text span { font-size: 0.75rem; color: #a5b4fc; opacity: 0.8; }

.sidebar-content { flex: 1; padding: 16px; overflow-y: auto; }

.new-chat-btn {
  width: 100%; padding: 10px 16px;
  background: rgba(255, 255, 255, 0.1); border: 1px dashed rgba(255, 255, 255, 0.3);
  border-radius: var(--radius); color: white; font-size: 0.9rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: var(--transition); margin-bottom: 16px;
}
.new-chat-btn:hover { background: rgba(255, 255, 255, 0.2); border-color: rgba(255, 255, 255, 0.5); }

.sidebar-section { margin-bottom: 20px; }
.sidebar-section h3 { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #a5b4fc; margin-bottom: 6px; font-weight: 600; }

.history-section { flex: 1; }
.history-list { display: flex; flex-direction: column; gap: 2px; margin-bottom: 10px; }
.history-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: var(--transition);
}
.history-item:hover { background: rgba(255, 255, 255, 0.08); }
.history-item.active { background: rgba(255, 255, 255, 0.15); }
.history-info { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.history-title { font-size: 0.82rem; color: rgba(255, 255, 255, 0.9); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-time { font-size: 0.65rem; color: rgba(255, 255, 255, 0.4); margin-top: 2px; }
.history-delete {
  width: 24px; height: 24px; border: none; background: transparent;
  color: rgba(255, 255, 255, 0.3); cursor: pointer; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: var(--transition); flex-shrink: 0;
}
.history-item:hover .history-delete { opacity: 1; }
.history-delete:hover { background: rgba(239, 68, 68, 0.3); color: white; }

.expand-btn {
  width: 100%; padding: 6px; border: none; background: transparent;
  color: #a5b4fc; font-size: 0.72rem; cursor: pointer; border-radius: 6px;
  transition: var(--transition);
}
.expand-btn:hover { background: rgba(255, 255, 255, 0.08); }

.no-history { text-align: center; font-size: 0.78rem; color: rgba(255, 255, 255, 0.3); padding: 16px 0; }

.agent-status-list { display: flex; flex-direction: column; gap: 6px; }
.agent-status-item { display: flex; align-items: center; gap: 10px; padding: 6px 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.05); font-size: 0.82rem; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #64748b; }
.status-dot.active { background: #34d399; box-shadow: 0 0 8px rgba(52, 211, 153, 0.5); }
.agent-name { color: rgba(255, 255, 255, 0.85); }

.sidebar-footer { padding: 12px 16px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.user-info { display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #6366f1, #8b5cf6); display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.user-detail { flex: 1; min-width: 0; }
.user-name { display: block; font-size: 0.82rem; font-weight: 600; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-role { display: block; font-size: 0.65rem; color: rgba(255, 255, 255, 0.4); }
.logout-btn { width: 32px; height: 32px; border: none; background: rgba(255, 255, 255, 0.06); border-radius: 8px; color: rgba(255, 255, 255, 0.4); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: var(--transition); flex-shrink: 0; }
.logout-btn:hover { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }

.main-content { flex: 1; overflow: hidden; }
.chat-container { height: 100%; display: flex; }
.chat-area { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.welcome-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; overflow-y: auto; padding: 24px; }
.messages-container { flex: 1; overflow-y: auto; padding: 24px; scroll-behavior: smooth; }
.input-area { padding: 0 24px 24px; }

.message-enter-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.message-enter-from { opacity: 0; transform: translateY(20px); }
.slide-panel-enter-active, .slide-panel-leave-active { transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-panel-enter-from, .slide-panel-leave-to { opacity: 0; transform: translateX(100%); }
</style>
