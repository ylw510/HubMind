import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

const TOKEN_KEY = 'hubmind_token'
const USER_KEY = 'hubmind_user'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setTokenState] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    api.get('/api/me')
      .then((res) => {
        setUser(res.data)
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setTokenState(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const setToken = (newToken, userData) => {
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
      if (userData) localStorage.setItem(USER_KEY, JSON.stringify(userData))
      setTokenState(newToken)
      setUser(userData || null)
    } else {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      setTokenState(null)
      setUser(null)
    }
  }

  const login = async (username, password) => {
    const { data } = await api.post('/api/login', { username, password })
    setToken(data.access_token, data.user)
    return data
  }

  const register = async (username, password) => {
    const { data } = await api.post('/api/register', { username, password })
    setToken(data.access_token, data.user)
    return data
  }

  const logout = () => setToken(null)

  const value = { user, token, loading, login, register, logout, setToken }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
