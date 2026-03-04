<script setup lang="ts">
import type { ExampleQuery } from '../api/agent'

defineProps<{
  examples: ExampleQuery[]
}>()

const emit = defineEmits<{
  select: [query: string]
}>()

const categoryIcons: Record<string, string> = {
  comprehensive: '🔍',
  data_analysis: '📊',
  competitor_analysis: '⚔️',
  inventory_check: '📦',
}

const categoryColors: Record<string, string> = {
  comprehensive: '#6366f1',
  data_analysis: '#0ea5e9',
  competitor_analysis: '#f59e0b',
  inventory_check: '#10b981',
}
</script>

<template>
  <div class="welcome-panel">
    <div class="welcome-hero fade-in-up">
      <div class="hero-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          <polyline points="7.5 4.21 12 6.81 16.5 4.21"/>
          <line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>
      </div>
      <h2>您好，我是 DataMind</h2>
      <p>您的电商数据分析智能助手。我可以帮您查询销售数据、分析竞品价格、监控库存预警。</p>
      <p class="sub-text">支持自然语言提问，多智能体协作为您提供全方位的数据洞察。</p>
    </div>

    <div class="examples-section">
      <h3 class="section-title fade-in-up" style="animation-delay: 0.1s">试试这些问题</h3>
      <div class="examples-grid">
        <button
          v-for="(example, idx) in examples"
          :key="idx"
          class="example-card fade-in-up"
          :style="{ animationDelay: `${0.15 + idx * 0.08}s`, '--accent': categoryColors[example.category] || '#6366f1' }"
          @click="emit('select', example.query)"
        >
          <div class="example-icon">{{ categoryIcons[example.category] || '💡' }}</div>
          <div class="example-content">
            <h4>{{ example.title }}</h4>
            <p>{{ example.description }}</p>
          </div>
          <svg class="arrow-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="agent-flow fade-in-up" style="animation-delay: 0.6s">
      <h3 class="section-title">多智能体协作流程</h3>
      <div class="flow-steps">
        <div class="flow-step">
          <div class="step-icon" style="background: #eef2ff; color: #6366f1;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>
            </svg>
          </div>
          <span>意图识别</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step">
          <div class="step-icon" style="background: #e0f2fe; color: #0ea5e9;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20V10M18 20V4M6 20v-4"/>
            </svg>
          </div>
          <span>数据查询</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step">
          <div class="step-icon" style="background: #fef3c7; color: #f59e0b;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/>
            </svg>
          </div>
          <span>竞品对比</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step">
          <div class="step-icon" style="background: #d1fae5; color: #10b981;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="m7.5 4.27 9 5.15M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            </svg>
          </div>
          <span>库存预警</span>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step">
          <div class="step-icon" style="background: #fce7f3; color: #ec4899;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          <span>生成报告</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome-panel {
  max-width: 720px;
  width: 100%;
}

.welcome-hero {
  text-align: center;
  margin-bottom: 36px;
}

.hero-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}

.welcome-hero h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.welcome-hero p {
  color: var(--text-secondary);
  font-size: 1rem;
  max-width: 480px;
  margin: 0 auto;
}

.welcome-hero .sub-text {
  font-size: 0.85rem;
  color: var(--text-light);
  margin-top: 4px;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-light);
  margin-bottom: 14px;
  text-align: center;
}

.examples-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 32px;
}

.example-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  text-align: left;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.example-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent);
  opacity: 0;
  transition: var(--transition);
}

.example-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.example-card:hover::before {
  opacity: 1;
}

.example-card:hover .arrow-icon {
  opacity: 1;
  transform: translateX(0);
}

.example-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
}

.example-content h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2px;
}

.example-content p {
  font-size: 0.75rem;
  color: var(--text-light);
}

.arrow-icon {
  flex-shrink: 0;
  color: var(--text-light);
  opacity: 0;
  transform: translateX(-8px);
  transition: var(--transition);
}

.agent-flow {
  margin-top: 8px;
}

.flow-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.flow-step span {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.flow-arrow {
  color: var(--text-light);
  font-size: 1.2rem;
  margin-bottom: 20px;
}
</style>
