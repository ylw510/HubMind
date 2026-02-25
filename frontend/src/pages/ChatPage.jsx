import React, { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Bot, User } from 'lucide-react'
import { chatAPI } from '../services/api'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'

function ChatPage() {
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])

  const mutation = useMutation({
    mutationFn: (msg) => chatAPI.chat(msg, chatHistory),
    onSuccess: (data) => {
      setChatHistory(data.chat_history)
      setMessage('')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!message.trim() || mutation.isPending) return
    mutation.mutate(message)
  }

  return (
    <div className="page-container">
      <h1 className="page-title">💬 智能对话</h1>
      <p className="page-description">与 HubMind 对话，探索 GitHub 世界</p>

      <div className="card" style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', marginBottom: '20px' }}>
          {chatHistory.length === 0 && (
            <div style={{ textAlign: 'center', color: '#8b949e', padding: '40px' }}>
              <Bot size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
              <p>开始与 HubMind 对话吧！</p>
              <p style={{ fontSize: '12px', marginTop: '8px' }}>
                试试："给我看看今天最火的5个项目"
              </p>
            </div>
          )}
          {chatHistory.map((msg, idx) => (
            <div
              key={idx}
              style={{
                marginBottom: '20px',
                display: 'flex',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                gap: '12px',
              }}
            >
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: msg.role === 'user' ? '#1f6feb' : '#238636',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              </div>
              <div
                style={{
                  maxWidth: '70%',
                  background: msg.role === 'user' ? '#1f6feb' : '#21262d',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  color: '#f0f6fc',
                }}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  <p style={{ margin: 0 }}>{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {mutation.isPending && (
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: '#238636',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Bot size={20} />
              </div>
              <div
                style={{
                  background: '#21262d',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  color: '#8b949e',
                }}
              >
                思考中...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            className="input"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="输入你的问题..."
            disabled={mutation.isPending}
            style={{ marginBottom: 0 }}
          />
          <button
            type="submit"
            className="button"
            disabled={!message.trim() || mutation.isPending}
          >
            <Send size={18} />
          </button>
        </form>
      </div>

      {mutation.isError && (
        <div className="error">
          错误: {mutation.error?.response?.data?.detail || mutation.error?.message}
        </div>
      )}
    </div>
  )
}

export default ChatPage
