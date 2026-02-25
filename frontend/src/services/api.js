import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

export default api
