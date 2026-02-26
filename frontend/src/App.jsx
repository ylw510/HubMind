import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { MessageSquare, TrendingUp, GitPullRequest, FileText, Heart, HelpCircle, Github, Settings, LogOut } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import ChatPage from './pages/ChatPage'
import TrendingPage from './pages/TrendingPage'
import PRPage from './pages/PRPage'
import IssuePage from './pages/IssuePage'
import HealthPage from './pages/HealthPage'
import QAPage from './pages/QAPage'
import GitHubBrowserPage from './pages/GitHubBrowserPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import SettingsPage from './pages/SettingsPage'
import './App.css'

function NavBar() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const navItems = [
    { path: '/', icon: MessageSquare, label: '对话', name: 'chat' },
    { path: '/trending', icon: TrendingUp, label: '热门项目', name: 'trending' },
    { path: '/github', icon: Github, label: 'GitHub浏览器', name: 'github' },
    { path: '/prs', icon: GitPullRequest, label: 'PR分析', name: 'prs' },
    { path: '/issues', icon: FileText, label: 'Issue管理', name: 'issues' },
    { path: '/health', icon: Heart, label: '健康度', name: 'health' },
    { path: '/qa', icon: HelpCircle, label: '问答', name: 'qa' },
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

  return (
    <div className="app">
      <NavBar />
      <main className="main-content">
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
      <Route path="/trending" element={<ProtectedLayout><TrendingPage /></ProtectedLayout>} />
      <Route path="/github" element={<ProtectedLayout><GitHubBrowserPage /></ProtectedLayout>} />
      <Route path="/prs" element={<ProtectedLayout><PRPage /></ProtectedLayout>} />
      <Route path="/issues" element={<ProtectedLayout><IssuePage /></ProtectedLayout>} />
      <Route path="/health" element={<ProtectedLayout><HealthPage /></ProtectedLayout>} />
      <Route path="/qa" element={<ProtectedLayout><QAPage /></ProtectedLayout>} />
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
