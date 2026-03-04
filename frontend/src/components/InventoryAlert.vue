<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  alerts: Record<string, any>
}>()

const urgentItems = computed(() => props.alerts?.alerts?.urgent || [])
const warningItems = computed(() => props.alerts?.alerts?.warning || [])
</script>

<template>
  <div class="inventory-panel">
    <div class="panel-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m7.5 4.27 9 5.15M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      </svg>
      <span>库存预警</span>
      <span v-if="urgentItems.length" class="count-badge urgent">
        {{ urgentItems.length }} 紧急
      </span>
      <span v-if="warningItems.length" class="count-badge warning">
        {{ warningItems.length }} 预警
      </span>
    </div>

    <div class="alert-list">
      <div
        v-for="(item, idx) in urgentItems"
        :key="`u-${idx}`"
        class="alert-item urgent fade-in-up"
        :style="{ animationDelay: `${idx * 0.08}s` }"
      >
        <div class="alert-icon urgent-icon">!</div>
        <div class="alert-info">
          <div class="alert-name">{{ item.product_name }}</div>
          <div class="alert-detail">
            库存 <strong>{{ item.stock }}</strong> 件 · 阈值 {{ item.threshold }} · {{ item.warehouse }}
          </div>
          <div class="alert-suggestion">{{ item.restock_suggestion }}</div>
        </div>
        <div class="stock-bar-container">
          <div class="stock-bar">
            <div
              class="stock-fill urgent-fill"
              :style="{ width: `${Math.min(100, (item.stock / item.threshold) * 100)}%` }"
            />
          </div>
          <span class="days-left">剩余 {{ item.days_of_stock }} 天</span>
        </div>
      </div>

      <div
        v-for="(item, idx) in warningItems"
        :key="`w-${idx}`"
        class="alert-item warning fade-in-up"
        :style="{ animationDelay: `${(urgentItems.length + idx) * 0.08}s` }"
      >
        <div class="alert-icon warning-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <div class="alert-info">
          <div class="alert-name">{{ item.product_name }}</div>
          <div class="alert-detail">
            库存 <strong>{{ item.stock }}</strong> 件 · 阈值 {{ item.threshold }} · {{ item.warehouse }}
          </div>
          <div class="alert-suggestion">{{ item.restock_suggestion }}</div>
        </div>
        <div class="stock-bar-container">
          <div class="stock-bar">
            <div
              class="stock-fill warning-fill"
              :style="{ width: `${Math.min(100, (item.stock / item.threshold) * 100)}%` }"
            />
          </div>
          <span class="days-left">剩余 {{ item.days_of_stock }} 天</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-panel {
  background: white;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fffbeb;
  border-bottom: 1px solid #fef3c7;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text);
}

.panel-header svg {
  color: #f59e0b;
}

.count-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

.count-badge.urgent {
  background: #fef2f2;
  color: #ef4444;
}

.count-badge.warning {
  background: #fffbeb;
  color: #f59e0b;
}

.alert-list {
  padding: 8px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: var(--transition);
}

.alert-item.urgent {
  background: #fef2f2;
}

.alert-item.warning {
  background: #fffbeb;
}

.alert-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  margin-top: 2px;
}

.urgent-icon {
  background: #ef4444;
  color: white;
}

.warning-icon {
  background: #f59e0b;
  color: white;
}

.alert-info {
  flex: 1;
  min-width: 0;
}

.alert-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text);
}

.alert-detail {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.alert-detail strong {
  color: var(--text);
}

.alert-suggestion {
  font-size: 0.72rem;
  color: var(--primary);
  font-weight: 500;
  margin-top: 4px;
}

.stock-bar-container {
  width: 80px;
  flex-shrink: 0;
  text-align: center;
}

.stock-bar {
  width: 100%;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.stock-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease-out;
}

.urgent-fill {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.warning-fill {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.days-left {
  font-size: 0.65rem;
  color: var(--text-light);
  margin-top: 4px;
  display: inline-block;
}
</style>
