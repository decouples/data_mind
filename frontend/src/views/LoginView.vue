<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await authStore.login(username.value.trim(), password.value)
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') handleLogin()
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="7.5 4.21 12 6.81 16.5 4.21"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
        </div>
        <h1>DataMind</h1>
        <p>电商数据与业务洞察智能体</p>
      </div>

      <div class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <div class="input-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
            <input
              v-model="username"
              type="text"
              placeholder="请输入用户名"
              autocomplete="username"
              @keydown="handleKeydown"
            />
          </div>
        </div>

        <div class="form-group">
          <label>密码</label>
          <div class="input-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input
              v-model="password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              @keydown="handleKeydown"
            />
          </div>
        </div>

        <Transition name="fade">
          <div v-if="error" class="error-msg">{{ error }}</div>
        </Transition>

        <button class="login-btn" :disabled="loading" @click="handleLogin">
          <span v-if="!loading">登 录</span>
          <div v-else class="spinner"></div>
        </button>

        <div class="demo-hint">
          <p>演示账号</p>
          <div class="demo-accounts">
            <span @click="username = 'admin'; password = 'admin123'">管理员 admin</span>
            <span @click="username = 'analyst'; password = 'analyst123'">分析师 analyst</span>
            <span @click="username = 'demo'; password = 'demo123'">演示 demo</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
  position: relative; overflow: hidden;
}

.login-bg { position: absolute; inset: 0; pointer-events: none; }
.bg-orb {
  position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.3;
}
.orb-1 { width: 500px; height: 500px; background: #6366f1; top: -10%; left: -5%; animation: float 20s ease-in-out infinite; }
.orb-2 { width: 400px; height: 400px; background: #0ea5e9; bottom: -5%; right: -5%; animation: float 15s ease-in-out infinite reverse; }
.orb-3 { width: 300px; height: 300px; background: #8b5cf6; top: 40%; left: 50%; animation: float 18s ease-in-out infinite 3s; }

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-30px) scale(1.05); }
}

.login-card {
  position: relative; z-index: 1;
  background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px; padding: 48px 40px; width: 420px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
  animation: fadeInUp 0.6s ease-out;
}

.login-header { text-align: center; margin-bottom: 36px; }
.logo-icon {
  width: 56px; height: 56px; margin: 0 auto 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 16px; display: flex; align-items: center; justify-content: center; color: white;
}
.login-header h1 { font-size: 1.6rem; font-weight: 700; color: white; letter-spacing: -0.02em; }
.login-header p { font-size: 0.85rem; color: rgba(255, 255, 255, 0.5); margin-top: 4px; }

.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 6px; font-weight: 500; }

.input-wrap {
  display: flex; align-items: center; gap: 10px;
  background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px; padding: 12px 16px; transition: all 0.2s ease;
}
.input-wrap:focus-within {
  border-color: #6366f1; background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
}
.input-wrap svg { color: rgba(255, 255, 255, 0.4); flex-shrink: 0; }
.input-wrap input {
  flex: 1; border: none; background: transparent; outline: none;
  color: white; font-size: 0.92rem; font-family: inherit;
}
.input-wrap input::placeholder { color: rgba(255, 255, 255, 0.3); }

.error-msg {
  padding: 10px 14px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px; color: #fca5a5; font-size: 0.82rem; margin-bottom: 16px;
}

.login-btn {
  width: 100%; padding: 14px; border: none; border-radius: 12px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white;
  font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease;
  display: flex; align-items: center; justify-content: center; min-height: 48px;
}
.login-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4); }
.login-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.spinner {
  width: 20px; height: 20px; border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.demo-hint { margin-top: 24px; text-align: center; }
.demo-hint p { font-size: 0.72rem; color: rgba(255, 255, 255, 0.35); margin-bottom: 8px; }
.demo-accounts { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
.demo-accounts span {
  padding: 4px 10px; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px; font-size: 0.72rem; color: rgba(255, 255, 255, 0.45);
  cursor: pointer; transition: all 0.2s ease;
}
.demo-accounts span:hover { background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border-color: rgba(99, 102, 241, 0.3); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
