import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, MessageSquare, Github, ChevronLeft, ChevronRight, Trash2, Settings } from 'lucide-react'

export default function Sidebar({
  sessions = [],
  currentSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  collapsed = false,
  onToggleCollapse,
}) {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // 按日期分组
  const today = new Date().toDateString()
  const todaySessions = filteredSessions.filter(s => {
    const sessionDate = s.updated_at ? new Date(s.updated_at).toDateString() : (s.created_at ? new Date(s.created_at).toDateString() : today)
    return sessionDate === today
  })

  const otherSessions = filteredSessions.filter(s => {
    const sessionDate = s.updated_at ? new Date(s.updated_at).toDateString() : (s.created_at ? new Date(s.created_at).toDateString() : today)
    return sessionDate !== today
  })

  return (
    <aside className={`chatbot-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="chatbot-sidebar-header">
        {!collapsed && (
          <>
            <button
              type="button"
              className="chatbot-sidebar-new-chat"
              onClick={onNewChat}
            >
              <Plus size={16} />
              <span>New chat</span>
            </button>
            {sessions.length > 0 && (
              <div className="chatbot-sidebar-search">
                <input
                  type="text"
                  placeholder="搜索对话..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="chatbot-sidebar-search-input"
                />
              </div>
            )}
          </>
        )}
        <button
          type="button"
          className="chatbot-sidebar-toggle"
          onClick={onToggleCollapse}
          title={collapsed ? '展开侧边栏' : '收起侧边栏'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {!collapsed && (
        <div className="chatbot-sidebar-content">
          {todaySessions.length > 0 && (
            <div className="chatbot-sidebar-section">
              <div className="chatbot-sidebar-section-title">Today</div>
              {todaySessions.map((session) => (
                <div
                  key={session.id}
                  className={`chatbot-sidebar-item-wrapper ${currentSessionId === session.id ? 'active' : ''}`}
                >
                  <button
                    type="button"
                    className={`chatbot-sidebar-item ${currentSessionId === session.id ? 'active' : ''}`}
                    onClick={() => onSelectSession(session.id)}
                  >
                    <MessageSquare size={16} />
                    <span className="chatbot-sidebar-item-text">{session.title}</span>
                  </button>
                  {onDeleteSession && (
                    <button
                      type="button"
                      className="chatbot-sidebar-item-delete"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteSession(session.id)
                      }}
                      title="删除对话"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {otherSessions.length > 0 && (
            <div className="chatbot-sidebar-section">
              <div className="chatbot-sidebar-section-title">Previous</div>
              {otherSessions.map((session) => (
                <div
                  key={session.id}
                  className={`chatbot-sidebar-item-wrapper ${currentSessionId === session.id ? 'active' : ''}`}
                >
                  <button
                    type="button"
                    className={`chatbot-sidebar-item ${currentSessionId === session.id ? 'active' : ''}`}
                    onClick={() => onSelectSession(session.id)}
                  >
                    <MessageSquare size={16} />
                    <span className="chatbot-sidebar-item-text">{session.title}</span>
                  </button>
                  {onDeleteSession && (
                    <button
                      type="button"
                      className="chatbot-sidebar-item-delete"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteSession(session.id)
                      }}
                      title="删除对话"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {filteredSessions.length === 0 && (
            <div className="chatbot-sidebar-empty">
              {searchQuery ? '未找到匹配的对话' : '暂无对话历史'}
            </div>
          )}
        </div>
      )}

      {!collapsed && (
        <div className="chatbot-sidebar-footer">
          <button
            type="button"
            className="chatbot-sidebar-settings"
            onClick={() => navigate('/settings')}
            title="设置"
          >
            <Settings size={18} />
            <span>设置</span>
          </button>
          <div className="chatbot-sidebar-brand">
            <Github size={20} />
            <span>HubMind</span>
          </div>
        </div>
      )}
    </aside>
  )
}
