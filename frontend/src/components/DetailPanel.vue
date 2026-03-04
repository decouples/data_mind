<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ChatResponse } from '../api/agent'

const props = defineProps<{
  data: Partial<ChatResponse>
}>()

const emit = defineEmits<{
  close: []
}>()

const activeTab = ref<'data' | 'logs' | 'competitor'>('data')

const agentLogs = computed(() => props.data.agent_logs || [])
const queryResult = computed(() => props.data.query_result || [])
const columns = computed(() => {
  if (!queryResult.value.length) return []
  return Object.keys(queryResult.value[0])
})

const competitorData = computed(() => {
  const cd = props.data.competitor_data
  if (!cd || cd.status !== 'ok') return null
  return cd.data
})

function agentIcon(agent: string): string {
  const icons: Record<string, string> = {
    supervisor: '🧠',
    data_analyst: '📊',
    competitor: '⚔️',
    inventory: '📦',
    reporter: '📝',
  }
  return icons[agent] || '🤖'
}

function agentLabel(agent: string): string {
  const labels: Record<string, string> = {
    supervisor: '主调度',
    data_analyst: '数据分析',
    competitor: '竞品分析',
    inventory: '库存预警',
    reporter: '报告生成',
  }
  return labels[agent] || agent
}
</script>

<template>
  <div class="detail-panel">
    <div class="panel-header">
      <h3>详细数据</h3>
      <button class="close-btn" @click="emit('close')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'data' }"
        @click="activeTab = 'data'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
        查询数据
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'logs' }"
        @click="activeTab = 'logs'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        智能体日志
      </button>
      <button
        v-if="competitorData"
        class="tab-btn"
        :class="{ active: activeTab === 'competitor' }"
        @click="activeTab = 'competitor'"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/>
        </svg>
        竞品数据
      </button>
    </div>

    <div class="panel-body">
      <!-- Data Tab -->
      <div v-if="activeTab === 'data'" class="data-tab fade-in">
        <div v-if="data.sql_query" class="sql-display">
          <span class="sql-label">SQL</span>
          <code>{{ data.sql_query }}</code>
        </div>

        <div v-if="queryResult.length" class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th v-for="col in columns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in queryResult" :key="idx">
                <td v-for="col in columns" :key="col">{{ row[col] ?? '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">暂无查询数据</div>
      </div>

      <!-- Logs Tab -->
      <div v-if="activeTab === 'logs'" class="logs-tab fade-in">
        <div class="log-timeline">
          <div
            v-for="(log, idx) in agentLogs"
            :key="idx"
            class="log-item fade-in-up"
            :style="{ animationDelay: `${idx * 0.1}s` }"
          >
            <div class="log-marker">
              <span class="log-icon">{{ agentIcon(log.agent) }}</span>
              <div v-if="idx < agentLogs.length - 1" class="log-line" />
            </div>
            <div class="log-content">
              <div class="log-header">
                <span class="log-agent">{{ agentLabel(log.agent) }}</span>
                <span class="log-action">{{ log.action }}</span>
              </div>
              <div class="log-detail">
                <span v-if="log.result">结果: {{ log.result }}</span>
                <span v-if="log.sql">SQL: {{ log.sql?.substring(0, 80) }}...</span>
                <span v-if="log.rows !== undefined">{{ log.rows }} 条记录</span>
                <span v-if="log.urgent !== undefined">紧急: {{ log.urgent }}, 预警: {{ log.warning }}</span>
                <span v-if="log.products">涉及 {{ log.products }} 个商品</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Competitor Tab -->
      <div v-if="activeTab === 'competitor' && competitorData" class="competitor-tab fade-in">
        <div v-for="(info, product) in competitorData" :key="String(product)" class="comp-product">
          <div class="comp-header">
            <h4>{{ product }}</h4>
            <span class="price-position" :class="info.price_position === '价格优势明显' ? 'good' : info.price_position === '价格偏高' ? 'bad' : 'neutral'">
              {{ info.price_position }}
            </span>
          </div>
          <div class="comp-our-price">我方售价: <strong>¥{{ info.our_price }}</strong> · 竞品均价: ¥{{ info.avg_competitor_price }}</div>
          <div class="comp-list">
            <div v-for="(c, cidx) in info.competitors" :key="cidx" class="comp-item">
              <span class="comp-name">{{ c.name }}</span>
              <span class="comp-price" :class="{ cheaper: c.price < info.our_price, pricier: c.price > info.our_price }">
                ¥{{ c.price }}
              </span>
              <span class="comp-sales">月销 {{ c.sales?.toLocaleString() }}</span>
              <span class="comp-platform">{{ c.platform }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-panel {
  width: 420px;
  min-width: 420px;
  border-left: 1px solid var(--border);
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.panel-header h3 {
  font-size: 1rem;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: var(--bg);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}

.close-btn:hover {
  background: #fef2f2;
  color: #ef4444;
}

.tab-bar {
  display: flex;
  padding: 8px 16px;
  gap: 4px;
  border-bottom: 1px solid var(--border-light);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
  font-weight: 500;
}

.tab-btn:hover {
  background: var(--bg);
}

.tab-btn.active {
  background: var(--primary-bg);
  color: var(--primary);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Data tab */
.sql-display {
  background: #f8fafc;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  overflow-x: auto;
}

.sql-label {
  display: inline-block;
  padding: 1px 6px;
  background: var(--primary);
  color: white;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.sql-display code {
  display: block;
  font-size: 0.78rem;
  color: var(--text-secondary);
  font-family: 'Fira Code', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

th {
  background: #f8fafc;
  padding: 8px 10px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
}

td {
  padding: 7px 10px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text);
  white-space: nowrap;
}

tr:hover td {
  background: #f8fafc;
}

/* Logs tab */
.log-timeline {
  padding-left: 4px;
}

.log-item {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}

.log-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 28px;
  flex-shrink: 0;
}

.log-icon {
  font-size: 1.1rem;
  z-index: 1;
}

.log-line {
  width: 2px;
  flex: 1;
  background: var(--border);
  margin-top: 4px;
}

.log-content {
  flex: 1;
  padding-bottom: 16px;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.log-agent {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text);
}

.log-action {
  font-size: 0.72rem;
  color: var(--text-light);
  background: var(--bg);
  padding: 1px 8px;
  border-radius: 10px;
}

.log-detail {
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Competitor tab */
.comp-product {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.comp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.comp-header h4 {
  font-size: 0.9rem;
  font-weight: 600;
}

.price-position {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 600;
}

.price-position.good { background: #d1fae5; color: #059669; }
.price-position.bad { background: #fef2f2; color: #dc2626; }
.price-position.neutral { background: #e0f2fe; color: #0284c7; }

.comp-our-price {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.comp-our-price strong {
  color: var(--primary);
}

.comp-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comp-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 0.78rem;
}

.comp-name {
  flex: 1;
  color: var(--text);
  font-weight: 500;
}

.comp-price {
  font-weight: 600;
}

.comp-price.cheaper { color: #059669; }
.comp-price.pricier { color: #dc2626; }

.comp-sales {
  color: var(--text-light);
  font-size: 0.72rem;
}

.comp-platform {
  padding: 1px 6px;
  background: var(--primary-bg);
  color: var(--primary);
  border-radius: 4px;
  font-size: 0.68rem;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-light);
  font-size: 0.85rem;
}
</style>
