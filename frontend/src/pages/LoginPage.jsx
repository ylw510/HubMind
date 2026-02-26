import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { BackendConnectionBanner } from '../components/BackendConnectionBanner'

function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail) {
        setError(detail)
      } else if (err.message === 'Network Error' || !err.response) {
        setError('无法连接服务器，请检查后端是否已启动')
      } else {
        setError(err.message || '登录失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <BackendConnectionBanner />
      <div className="auth-card card">
        <h1 className="auth-title">登录 HubMind</h1>
        <p className="auth-subtitle">使用你的账号登录</p>
        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error">{error}</div>}
          <input
            type="text"
            className="input"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
          <input
            type="password"
            className="input"
            placeholder="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <button type="submit" className="button auth-submit" disabled={loading}>
            <LogIn size={18} />
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
        <p className="auth-footer">
          还没有账号？ <Link to="/register" className="link-accent">注册</Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
