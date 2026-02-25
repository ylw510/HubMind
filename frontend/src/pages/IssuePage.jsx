import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FileText, CheckCircle } from 'lucide-react'
import { issueAPI } from '../services/api'

function IssuePage() {
  const [repo, setRepo] = useState('')
  const [text, setText] = useState('')
  const [assignees, setAssignees] = useState('')
  const [labels, setLabels] = useState('')

  const mutation = useMutation({
    mutationFn: () => issueAPI.createIssue(
      repo,
      text,
      assignees ? assignees.split(',').map(s => s.trim()) : null,
      labels ? labels.split(',').map(s => s.trim()) : null
    ),
    onSuccess: () => {
      setText('')
      setAssignees('')
      setLabels('')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!repo.trim() || !text.trim() || mutation.isPending) return
    mutation.mutate()
  }

  return (
    <div className="page-container">
      <h1 className="page-title">📋 Issue 管理</h1>
      <p className="page-description">使用自然语言创建 GitHub Issue</p>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="input"
            placeholder="仓库名 (如: owner/repo)"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            required
          />
          <textarea
            className="input"
            placeholder="Issue 描述 (自然语言，如: 添加暗色模式支持)"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            required
            style={{ resize: 'vertical' }}
          />
          <input
            type="text"
            className="input"
            placeholder="指派给 (可选，用逗号分隔，如: user1,user2)"
            value={assignees}
            onChange={(e) => setAssignees(e.target.value)}
          />
          <input
            type="text"
            className="input"
            placeholder="标签 (可选，用逗号分隔，如: bug,enhancement)"
            value={labels}
            onChange={(e) => setLabels(e.target.value)}
          />
          <button
            type="submit"
            className="button"
            disabled={!repo.trim() || !text.trim() || mutation.isPending}
          >
            <FileText size={18} style={{ marginRight: '8px' }} />
            {mutation.isPending ? '创建中...' : '创建 Issue'}
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
          <div className="success">
            <CheckCircle size={18} style={{ marginRight: '8px', display: 'inline' }} />
            Issue 创建成功！
          </div>
          <div style={{ marginTop: '16px' }}>
            <p><strong>Issue #{mutation.data.number}:</strong> {mutation.data.title}</p>
            <p style={{ marginTop: '8px' }}>
              <a
                href={mutation.data.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#58a6ff' }}
              >
                查看 Issue →
              </a>
            </p>
            {mutation.data.similar_issues && mutation.data.similar_issues.length > 0 && (
              <div style={{ marginTop: '16px', padding: '12px', background: '#1c2128', borderRadius: '6px' }}>
                <p style={{ fontSize: '12px', color: '#8b949e', marginBottom: '8px' }}>
                  ⚠️ 发现 {mutation.data.similar_issues.length} 个相似 Issue
                </p>
                {mutation.data.similar_issues.slice(0, 3).map((issue, idx) => (
                  <a
                    key={idx}
                    href={issue.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ display: 'block', color: '#58a6ff', fontSize: '12px', marginTop: '4px' }}
                  >
                    #{issue.number}: {issue.title}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default IssuePage
