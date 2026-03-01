import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { MessageSquare, Settings, LogOut } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import ChatPage from './pages/ChatPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import SettingsPage from './pages/SettingsPage'
import './App.css'

function NavBar() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const navItems = [
    { path: '/', icon: MessageSquare, label: '对话', name: 'chat' },
    { path: '/settings', icon: Settings, label: '设置', name: 'settings' },
  ]

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <h1>HubMind</h1>
      </div>
      <div className="nav-links">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          )
        })}
        <div className="nav-user">
          <span className="nav-username">{user?.username}</span>
          <button type="button" className="nav-logout" onClick={logout} title="退出登录">
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </nav>
  )
}

function ProtectedLayout({ children }) {
  const { token, loading } = useAuth()
  const location = useLocation()
  const isChatPage = location.pathname === '/'

  if (loading) {
    return (
      <div className="app">
        <div className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div className="loading">加载中...</div>
        </div>
      </div>
    )
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  // ChatPage 使用自己的布局，不显示 NavBar
  if (isChatPage) {
    return (
      <div className="app" style={{ display: 'block' }}>
        <main className="main-content">
          {children}
        </main>
      </div>
    )
  }

  // 其他页面显示 NavBar
  return (
    <div className="app">
      <NavBar />
      <main className="main-content settings-layout" style={{ marginLeft: '260px' }}>
        {children}
      </main>
    </div>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<ProtectedLayout><ChatPage /></ProtectedLayout>} />
      <Route path="/settings" element={<ProtectedLayout><SettingsPage /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  )
}

export default App
