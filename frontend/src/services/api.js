import axios from 'axios'

const STORAGE_API_URL_KEY = 'hubmind_api_url'
const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/** 0.0.0.0 仅用于服务端监听，浏览器必须用 127.0.0.1 或 localhost */
function normalizeApiUrl(url) {
  if (!url || !url.trim()) return url
  const u = url.trim().replace(/\/$/, '')
  if (u.includes('0.0.0.0')) {
    return u.replace(/0\.0\.0\.0/g, '127.0.0.1')
  }
  return u
}

function getStoredApiUrl() {
  try {
    const stored = localStorage.getItem(STORAGE_API_URL_KEY)
    if (stored && stored.trim()) {
      const normalized = normalizeApiUrl(stored)
      if (normalized !== stored) {
        localStorage.setItem(STORAGE_API_URL_KEY, normalized)
      }
      return normalized
    }
  } catch (_) {}
  return DEFAULT_API_URL
}

const api = axios.create({
  baseURL: getStoredApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hubmind_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** 获取当前请求的后端地址 */
export function getApiBaseUrl() {
  return api.defaults.baseURL || getStoredApiUrl()
}

/** 修改后端地址（如无法连接时可改为 http://127.0.0.1:8000 等） */
export function setApiBaseUrl(url) {
  const raw = (url || '').trim().replace(/\/$/, '') || DEFAULT_API_URL
  const u = normalizeApiUrl(raw)
  localStorage.setItem(STORAGE_API_URL_KEY, u)
  api.defaults.baseURL = u
  return u
}

/** 检测后端是否可达 */
export function checkBackendHealth() {
  return api.get('/api/health').then(() => true).catch(() => false)
}

export const chatAPI = {
  chat: async (message, chatHistory = []) => {
    const response = await api.post('/api/chat', {
      message,
      chat_history: chatHistory,
    })
    return response.data
  },
}

export const trendingAPI = {
  getTrending: async (language = null, since = 'daily', limit = 10) => {
    const response = await api.post('/api/trending', {
      language,
      since,
      limit,
    })
    return response.data
  },
}

export const prAPI = {
  getPRs: async (repo, limit = 10, valuable = false) => {
    const response = await api.post('/api/prs', {
      repo,
      limit,
      valuable,
    })
    return response.data
  },
  analyzePR: async (repo, prNumber) => {
    const response = await api.post('/api/analyze-pr', {
      repo,
      pr_number: prNumber,
    })
    return response.data
  },
}

export const issueAPI = {
  createIssue: async (repo, text, assignees = null, labels = null) => {
    const response = await api.post('/api/create-issue', {
      repo,
      text,
      assignees,
      labels,
    })
    return response.data
  },
}

export const qaAPI = {
  askQuestion: async (repo, question) => {
    const response = await api.post('/api/qa', {
      repo,
      question,
    })
    return response.data
  },
}

export const healthAPI = {
  getHealth: async (repo, days = 30) => {
    const response = await api.post('/api/health-repo', {
      repo,
      days,
    })
    return response.data
  },
}

export const githubAPI = {
  getRepoInfo: async (repo) => {
    const response = await api.post('/api/github/repo-info', {
      repo,
    })
    return response.data
  },
  getRepoFiles: async (repo, path = '') => {
    const response = await api.post('/api/github/repo-files', {
      repo,
      path,
    })
    return response.data
  },
  getReadme: async (repo) => {
    const response = await api.post('/api/github/readme', {
      repo,
    })
    return response.data
  },
}

export default api
