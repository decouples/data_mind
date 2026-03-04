<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  send: [query: string]
}>()

const input = ref('')

function handleSend() {
  const query = input.value.trim()
  if (!query) return
  emit('send', query)
  input.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="input-wrapper">
    <div class="input-box" :class="{ focused: false, disabled: loading }">
      <textarea
        v-model="input"
        :disabled="loading"
        placeholder="输入您的问题，例如：上个月华东区哪款外套卖得最好？"
        rows="1"
        @keydown="handleKeydown"
      />
      <button
        class="send-btn"
        :disabled="!input.trim() || loading"
        @click="handleSend"
      >
        <svg v-if="!loading" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        <div v-else class="loading-spinner" />
      </button>
    </div>
    <p class="input-hint">
      按 Enter 发送 · 支持自然语言提问 · 多智能体协作分析
    </p>
  </div>
</template>

<style scoped>
.input-wrapper {
  max-width: 100%;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-card);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 12px 12px 12px 20px;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.input-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1), var(--shadow);
}

.input-box.disabled {
  opacity: 0.7;
}

textarea {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text);
  background: transparent;
  resize: none;
  font-family: inherit;
  max-height: 120px;
}

textarea::placeholder {
  color: var(--text-light);
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: var(--primary);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: scale(1.05);
}

.send-btn:disabled {
  background: var(--border);
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.input-hint {
  text-align: center;
  font-size: 0.72rem;
  color: var(--text-light);
  margin-top: 8px;
}
</style>
