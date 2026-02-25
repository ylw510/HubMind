import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { HelpCircle, Bot } from 'lucide-react'
import { qaAPI } from '../services/api'
import ReactMarkdown from 'react-markdown'

function QAPage() {
  const [repo, setRepo] = useState('')
  const [question, setQuestion] = useState('')

  const mutation = useMutation({
    mutationFn: () => qaAPI.askQuestion(repo, question),
    onSuccess: () => {
      setQuestion('')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!repo.trim() || !question.trim() || mutation.isPending) return
    mutation.mutate()
  }

  return (
    <div className="page-container">
      <h1 className="page-title">❓ 智能问答</h1>
      <p className="page-description">询问关于 GitHub 仓库的问题</p>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="input"
            placeholder="仓库名 (如: microsoft/vscode)"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            required
          />
          <textarea
            className="input"
            placeholder="你的问题 (如: 这个项目使用什么构建工具？)"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={4}
            required
            style={{ resize: 'vertical' }}
          />
          <button
            type="submit"
            className="button"
            disabled={!repo.trim() || !question.trim() || mutation.isPending}
          >
            <HelpCircle size={18} style={{ marginRight: '8px' }} />
            {mutation.isPending ? '思考中...' : '提问'}
          </button>
        </form>
      </div>

      {mutation.isError && (
        <div className="error">
          错误: {mutation.error?.response?.data?.detail || mutation.error?.message}
        </div>
      )}

      {mutation.isSuccess && (
        <div className="card">
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: '#238636',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Bot size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ color: '#8b949e', fontSize: '12px', marginBottom: '4px' }}>
                问题: {mutation.data.question}
              </p>
              <div style={{ color: '#f0f6fc' }}>
                <ReactMarkdown>{mutation.data.answer}</ReactMarkdown>
              </div>
            </div>
          </div>
          {mutation.data.sources && mutation.data.sources.length > 0 && (
            <div style={{ marginTop: '16px', padding: '12px', background: '#1c2128', borderRadius: '6px' }}>
              <p style={{ fontSize: '12px', color: '#8b949e', marginBottom: '8px' }}>来源:</p>
              {mutation.data.sources.map((source, idx) => (
                <p key={idx} style={{ fontSize: '12px', color: '#58a6ff', marginTop: '4px' }}>
                  {source}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default QAPage
