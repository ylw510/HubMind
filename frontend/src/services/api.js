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
  chat: async (message, chatHistory = [], repo = null, sessionId = null, onChunk = null) => {
    // 如果 sessionId 是 'current' 或无效值，转换为 null
    const validSessionId = (sessionId && sessionId !== 'current' && typeof sessionId === 'number') ? sessionId : null

    // 如果提供了 onChunk 回调，使用流式模式
    if (onChunk) {
      return new Promise((resolve, reject) => {
        const token = localStorage.getItem('hubmind_token')
        const baseURL = getStoredApiUrl()

        fetch(`${baseURL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            message,
            chat_history: chatHistory,
            repo: repo || null,
            session_id: validSessionId,
          }),
        })
          .then(async (response) => {
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let fullResponse = ''
            let buffer = ''

            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })
              const lines = buffer.split('\n')
              buffer = lines.pop() || '' // 保留最后一个不完整的行

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6))
                    if (data.chunk) {
                      fullResponse += data.chunk
                      onChunk(data.chunk, data.done || false)
                    }
                    if (data.done) {
                      resolve({
                        response: fullResponse,
                        chat_history: [
                          ...chatHistory,
                          { role: 'user', content: message },
                          { role: 'assistant', content: fullResponse },
                        ],
                      })
                      return
                    }
                  } catch (e) {
                    console.error('Error parsing SSE data:', e)
                  }
                }
              }
            }
          })
          .catch(reject)
      })
    } else {
      // 非流式模式（向后兼容）
      const response = await api.post('/api/chat', {
        message,
        chat_history: chatHistory,
        repo: repo || null,
        session_id: validSessionId,
      })
      return response.data
    }
  },
  getSessions: async () => {
    const response = await api.get('/api/chat/sessions')
    return response.data
  },
  getSession: async (sessionId) => {
    const response = await api.get(`/api/chat/sessions/${sessionId}`)
    return response.data
  },
  createSession: async (title = 'New chat', repo = null) => {
    const response = await api.post('/api/chat/sessions', {
      title,
      repo,
    })
    return response.data
  },
  updateSession: async (sessionId, title = null, repo = null) => {
    const response = await api.put(`/api/chat/sessions/${sessionId}`, {
      title,
      repo,
    })
    return response.data
  },
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/api/chat/sessions/${sessionId}`)
    return response.data
  },
  saveMessages: async (sessionId, messages) => {
    const response = await api.post(`/api/chat/sessions/${sessionId}/messages`, {
      session_id: sessionId,
      messages,
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
  parseIssue: async (repo, text) => {
    const response = await api.post('/api/parse-issue', {
      repo,
      text,
    })
    return response.data
  },
  createIssueDraft: async (repo, title, body, assignees = null, labels = null) => {
    const response = await api.post('/api/create-issue-draft', {
      repo,
      title,
      body,
      assignees,
      labels,
    })
    return response.data
  },
  getRepoLabels: async (repo) => {
    const response = await api.get(`/api/github/repo-labels?repo=${encodeURIComponent(repo)}`)
    return response.data
  },
  getRepoCollaborators: async (repo) => {
    const response = await api.get(`/api/github/repo-collaborators?repo=${encodeURIComponent(repo)}`)
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
  getUserRepos: async () => {
    try {
      const response = await api.get('/api/github/user-repos')
      return response.data
    } catch (error) {
      // 返回错误信息，让组件可以显示
      console.error('获取仓库列表失败:', error)
      console.error('错误详情:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      })

      let errorMessage = '获取仓库列表失败'
      if (error.response?.status === 404) {
        errorMessage = 'API 路由未找到。请检查后端服务是否正常运行。'
      } else if (error.response?.status === 401) {
        errorMessage = error.response?.data?.detail || '未登录或登录已过期。请重新登录。'
      } else if (error.response?.status === 400) {
        errorMessage = error.response?.data?.detail || '未配置 GitHub Token。请在设置页面配置你的 GitHub Token。'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }

      return { repos: [], count: 0, error: errorMessage }
    }
  },
  searchRepos: async (query, limit = 20) => {
    try {
      const response = await api.post('/api/github/search-repos', {
        query,
        limit,
      })
      return response.data
    } catch (error) {
      console.error('搜索仓库失败:', error)
      let errorMessage = '搜索仓库失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      return { repos: [], count: 0, error: errorMessage }
    }
  },
  checkIssuePermission: async (repo) => {
    try {
      const response = await api.post('/api/github/check-issue-permission', {
        repo,
      })
      return response.data
    } catch (error) {
      console.error('检查权限失败:', error)
      return {
        can_create: false,
        reason: 'error',
        message: error.response?.data?.detail || '检查权限失败',
        repo_info: null,
      }
    }
  },
}

export default api
