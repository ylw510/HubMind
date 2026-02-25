import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { MessageSquare, TrendingUp, GitPullRequest, FileText, Heart, HelpCircle } from 'lucide-react'
import ChatPage from './pages/ChatPage'
import TrendingPage from './pages/TrendingPage'
import PRPage from './pages/PRPage'
import IssuePage from './pages/IssuePage'
import HealthPage from './pages/HealthPage'
import QAPage from './pages/QAPage'
import './App.css'

function NavBar() {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: MessageSquare, label: '对话', name: 'chat' },
    { path: '/trending', icon: TrendingUp, label: '热门项目', name: 'trending' },
    { path: '/prs', icon: GitPullRequest, label: 'PR分析', name: 'prs' },
    { path: '/issues', icon: FileText, label: 'Issue管理', name: 'issues' },
    { path: '/health', icon: Heart, label: '健康度', name: 'health' },
    { path: '/qa', icon: HelpCircle, label: '问答', name: 'qa' },
  ]

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <h1>🤖 HubMind</h1>
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
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <NavBar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/trending" element={<TrendingPage />} />
            <Route path="/prs" element={<PRPage />} />
            <Route path="/issues" element={<IssuePage />} />
            <Route path="/health" element={<HealthPage />} />
            <Route path="/qa" element={<QAPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
