<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
} from 'echarts/components'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
])

const props = defineProps<{
  config: Record<string, any>
}>()

const show = ref(false)

onMounted(() => {
  setTimeout(() => { show.value = true }, 100)
})

const COLORS = [
  '#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b',
]

const chartOption = computed(() => {
  const opt = props.config?.option
  if (!opt) return {}

  return {
    ...opt,
    color: opt.color || COLORS,
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 800,
    animationEasing: 'cubicOut',
    grid: {
      ...opt.grid,
      left: '3%',
      right: '4%',
      bottom: '8%',
      containLabel: true,
    },
    tooltip: {
      ...opt.tooltip,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b', fontSize: 13 },
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
    },
  }
})
</script>

<template>
  <div class="chart-panel">
    <div v-if="config.title" class="chart-title">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 20V10M18 20V4M6 20v-4"/>
      </svg>
      {{ config.title }}
    </div>
    <Transition name="chart-fade">
      <VChart
        v-if="show"
        :option="chartOption"
        :autoresize="true"
        class="chart-instance"
      />
    </Transition>
  </div>
</template>

<style scoped>
.chart-panel {
  background: white;
  padding: 16px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-light);
}

.chart-title svg {
  color: var(--primary);
}

.chart-instance {
  width: 100%;
  height: 320px;
}

.chart-fade-enter-active {
  transition: all 0.6s ease-out;
}

.chart-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
</style>
