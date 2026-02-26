import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { BackendConnectionBanner } from '../components/BackendConnectionBanner'

function RegisterPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }
    if (password.length < 6) {
      setError('密码至少 6 位')
      return
    }
    setLoading(true)
    try {
      await register(username, password)
      navigate('/', { replace: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail) {
        setError(detail)
      } else if (err.message === 'Network Error' || !err.response) {
        setError('无法连接服务器，请检查后端是否已启动')
      } else {
        setError(err.message || '注册失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <BackendConnectionBanner />
      <div className="auth-card card">
        <h1 className="auth-title">注册 HubMind</h1>
        <p className="auth-subtitle">创建你的账号</p>
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
            placeholder="密码（至少 6 位）"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          <input
            type="password"
            className="input"
            placeholder="确认密码"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          <button type="submit" className="button auth-submit" disabled={loading}>
            <UserPlus size={18} />
            {loading ? '注册中...' : '注册'}
          </button>
        </form>
        <p className="auth-footer">
          已有账号？ <Link to="/login" className="link-accent">登录</Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
