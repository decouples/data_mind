<script setup lang="ts">
import { computed, ref } from 'vue'
import { marked } from 'marked'
import type { Message } from '../stores/chat'
import { submitFeedback } from '../api/agent'
import { useChatStore } from '../stores/chat'
import ChartPanel from './ChartPanel.vue'
import InventoryAlert from './InventoryAlert.vue'

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits<{
  viewDetail: [message: Message]
}>()

const chatStore = useChatStore()
const sqlExpanded = ref(false)
const feedbackLoading = ref(false)
const currentRating = ref(props.message.feedback ?? 0)

const isUser = computed(() => props.message.role === 'user')
const htmlContent = computed(() => {
  if (!props.message.content) return ''
  return marked.parse(props.message.content) as string
})
const hasData = computed(() => !!props.message.data && Object.keys(props.message.data).length > 0)
const hasChart = computed(() => !!props.message.data?.charts_config?.option)
const hasInventory = computed(() => {
  const alerts = props.message.data?.inventory_alerts
  return alerts && ((alerts as any).urgent_count > 0 || (alerts as any).warning_count > 0)
})
const intentLabel = computed(() => {
  const map: Record<string, string> = {
    data_query: '数据查询',
    data_analysis: '数据分析',
    competitor_analysis: '竞品分析',
    inventory_check: '库存预警',
    comprehensive: '综合分析',
  }
  return map[props.message.data?.intent || ''] || ''
})
const sqlQuery = computed(() => props.message.data?.sql_query || '')
const stages = computed(() => props.message.stages || [])
const isLoading = computed(() => props.message.loading)
const hasReport = computed(() => !!props.message.content && !isLoading.value)

async function handleFeedback(rating: number) {
  if (feedbackLoading.value) return
  const newRating = currentRating.value === rating ? 0 : rating
  feedbackLoading.value = true
  try {
    if (newRating !== 0) {
      await submitFeedback(
        props.message.id,
        newRating,
        chatStore.activeSessionId,
        props.message.data?.query,
      )
    }
    currentRating.value = newRating
    // Persist to message so it survives re-renders
    const session = chatStore.activeSession
    if (session) {
      const msg = session.messages.find(m => m.id === props.message.id)
      if (msg) msg.feedback = newRating
    }
  } catch { /* silently ignore */ }
  finally { feedbackLoading.value = false }
}
</script>

<template>
  <div class="message-row" :class="{ 'user-row': isUser }">
    <div class="avatar" :class="{ 'user-avatar': isUser, 'ai-avatar': !isUser }">
      <svg v-if="isUser" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
      <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      </svg>
    </div>

    <div class="message-body" :class="{ 'user-body': isUser }">
      <div v-if="isUser" class="user-bubble">{{ message.content }}</div>

      <div v-else class="ai-bubble">
        <!-- Stage progress -->
        <div v-if="stages.length" class="stage-list">
          <div v-for="s in stages" :key="s.node" class="stage-item" :class="{ done: s.done }">
            <span class="stage-dot" :class="{ active: !s.done && isLoading }"></span>
            <span class="stage-text">{{ s.message }}</span>
          </div>
        </div>

        <!-- Intent badge -->
        <div v-if="intentLabel" class="intent-badge fade-in">
          <span class="badge-dot"></span>
          {{ intentLabel }}
        </div>

        <!-- SQL collapsible -->
        <div v-if="sqlQuery" class="sql-toggle fade-in" @click="sqlExpanded = !sqlExpanded">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
          </svg>
          <span>SQL 查询</span>
          <svg class="chevron" :class="{ rotated: sqlExpanded }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
        <Transition name="collapse">
          <div v-if="sqlExpanded && sqlQuery" class="sql-block">
            <code>{{ sqlQuery }}</code>
          </div>
        </Transition>

        <!-- Chart -->
        <div v-if="hasChart" class="chart-wrapper scale-in">
          <ChartPanel :config="message.data!.charts_config!" />
        </div>

        <!-- Inventory alerts -->
        <div v-if="hasInventory" class="inventory-wrapper scale-in">
          <InventoryAlert :alerts="message.data!.inventory_alerts!" />
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading && !hasReport" class="loading-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
          <p class="loading-text">{{ stages.length > 1 ? '智能体正在协作分析中...' : '正在处理...' }}</p>
        </div>

        <!-- Report text -->
        <div v-if="hasReport" class="report-content markdown-body fade-in" v-html="htmlContent" />

        <!-- Action bar -->
        <div v-if="hasData && !isLoading" class="action-bar">
          <button class="detail-btn" @click="emit('viewDetail', message)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
            </svg>
            查看完整数据
          </button>

          <div class="feedback-group">
            <button
              class="feedback-btn"
              :class="{ active: currentRating === 1 }"
              :disabled="feedbackLoading"
              title="这个回答很有帮助"
              @click="handleFeedback(1)"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" :fill="currentRating === 1 ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
              </svg>
            </button>
            <button
              class="feedback-btn"
              :class="{ active: currentRating === -1 }"
              :disabled="feedbackLoading"
              title="这个回答需要改进"
              @click="handleFeedback(-1)"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" :fill="currentRating === -1 ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-row {
  display: flex; gap: 12px; margin-bottom: 24px;
  animation: fadeInUp 0.4s ease-out;
}
.message-row.user-row { flex-direction: row-reverse; }

.avatar {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}
.user-avatar { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; }
.ai-avatar { background: linear-gradient(135deg, #e0e7ff, #c7d2fe); color: var(--primary); }

.message-body { max-width: 75%; min-width: 200px; }

.user-bubble {
  background: var(--primary); color: white;
  padding: 12px 18px; border-radius: 16px 16px 4px 16px;
  font-size: 0.92rem; line-height: 1.6; box-shadow: var(--shadow-sm);
}

.ai-bubble {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 16px 16px 16px 4px; padding: 18px 20px; box-shadow: var(--shadow-sm);
}

.stage-list { margin-bottom: 12px; }
.stage-item {
  display: flex; align-items: center; gap: 8px;
  padding: 3px 0; font-size: 0.78rem; color: var(--text-light);
  transition: all 0.3s ease;
}
.stage-item.done { color: var(--text-secondary); }
.stage-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--border); flex-shrink: 0; transition: all 0.3s ease;
}
.stage-item.done .stage-dot { background: var(--success); }
.stage-dot.active { background: var(--primary); animation: pulse 1.2s ease-in-out infinite; }

.intent-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; background: var(--primary-bg); color: var(--primary);
  border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin-bottom: 12px;
}
.badge-dot { width: 6px; height: 6px; background: var(--primary); border-radius: 50%; }

.sql-toggle {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; background: #f8fafc; border: 1px solid var(--border-light);
  border-radius: 8px; font-size: 0.78rem; color: var(--text-secondary);
  cursor: pointer; margin-bottom: 8px; transition: var(--transition); user-select: none;
}
.sql-toggle:hover { background: var(--primary-bg); color: var(--primary); border-color: var(--primary-light); }
.chevron { transition: transform 0.2s ease; }
.chevron.rotated { transform: rotate(180deg); }

.sql-block {
  background: #f8fafc; border: 1px solid var(--border-light); border-radius: 8px;
  padding: 10px 14px; margin-bottom: 14px; overflow-x: auto;
}
.sql-block code {
  font-size: 0.8rem; color: var(--text-secondary);
  font-family: 'Fira Code', 'Consolas', monospace;
  white-space: pre-wrap; word-break: break-all; line-height: 1.5;
}

.collapse-enter-active, .collapse-leave-active { transition: all 0.25s ease; overflow: hidden; }
.collapse-enter-from, .collapse-leave-to { opacity: 0; max-height: 0; margin-bottom: 0; padding: 0 14px; }
.collapse-enter-to, .collapse-leave-from { max-height: 200px; opacity: 1; }

.chart-wrapper { margin: 14px 0; border-radius: 10px; overflow: hidden; border: 1px solid var(--border-light); }
.inventory-wrapper { margin: 14px 0; }

.loading-content { display: flex; align-items: center; gap: 12px; padding: 4px 0; }
.typing-indicator { display: flex; gap: 4px; }
.typing-indicator span {
  width: 8px; height: 8px; background: var(--primary-light);
  border-radius: 50%; animation: bounce 1.4s ease-in-out infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
.loading-text { font-size: 0.85rem; color: var(--text-secondary); }

.report-content { font-size: 0.9rem; line-height: 1.7; color: var(--text); }

.action-bar {
  margin-top: 14px; padding-top: 12px;
  border-top: 1px solid var(--border-light);
  display: flex; align-items: center; gap: 8px;
}
.detail-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; background: var(--primary-bg); color: var(--primary);
  border: 1px solid transparent; border-radius: 8px;
  font-size: 0.8rem; font-weight: 500; cursor: pointer; transition: var(--transition);
}
.detail-btn:hover { background: var(--primary); color: white; }

.feedback-group {
  display: flex; gap: 4px; margin-left: auto;
}
.feedback-btn {
  width: 32px; height: 32px; border: 1px solid var(--border-light);
  background: transparent; border-radius: 8px;
  color: var(--text-light); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: var(--transition);
}
.feedback-btn:hover { border-color: var(--primary-light); color: var(--primary); background: var(--primary-bg); }
.feedback-btn.active:first-child { border-color: #10b981; color: #10b981; background: rgba(16, 185, 129, 0.08); }
.feedback-btn.active:last-child { border-color: #ef4444; color: #ef4444; background: rgba(239, 68, 68, 0.08); }
.feedback-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.fade-in { animation: fadeIn 0.3s ease-out; }
</style>
