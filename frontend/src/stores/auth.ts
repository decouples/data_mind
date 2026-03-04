import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '../api/agent'
import { login as apiLogin, getMe } from '../api/agent'

const TOKEN_KEY = 'datamind_token'
const USER_KEY = 'datamind_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<UserInfo | null>(loadUser())

  const isLoggedIn = computed(() => !!token.value)
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')
  const roleName = computed(() => user.value?.role_display || '')

  function loadUser(): UserInfo | null {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  async function login(username: string, password: string) {
    const result = await apiLogin(username, password)
    token.value = result.access_token
    user.value = result.user
    localStorage.setItem(TOKEN_KEY, result.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(result.user))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function refreshUser() {
    try {
      const me = await getMe()
      user.value = me
      localStorage.setItem(USER_KEY, JSON.stringify(me))
    } catch {
      logout()
    }
  }

  return { token, user, isLoggedIn, displayName, roleName, login, logout, refreshUser }
})
