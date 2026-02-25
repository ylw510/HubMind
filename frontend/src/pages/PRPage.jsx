import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GitPullRequest, Star, MessageSquare, ExternalLink } from 'lucide-react'
import { prAPI } from '../services/api'

function PRPage() {
  const [repo, setRepo] = useState('')
  const [limit, setLimit] = useState(10)
  const [valuable, setValuable] = useState(false)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['prs', repo, limit, valuable],
    queryFn: () => prAPI.getPRs(repo, limit, valuable),
    enabled: false,
    retry: 1,
    onError: (err) => {
      console.error('PR API Error:', err)
    },
    onSuccess: (data) => {
      console.log('PR API Success:', data)
    }
  })

  const handleSearch = () => {
    if (!repo.trim()) {
      alert('请输入仓库名（格式：owner/repo）')
      return
    }
    // Validate repo format
    if (!repo.includes('/')) {
      alert('仓库名格式不正确，应为：owner/repo（如：microsoft/vscode）')
      return
    }
    refetch()
  }

  return (
    <div className="page-container">
      <h1 className="page-title">📝 PR 分析</h1>
      <p className="page-description">查看和分析仓库的 Pull Requests</p>

      <div className="card">
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input"
            placeholder="仓库名 (如: microsoft/vscode)"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}
          />
          <input
            type="number"
            className="input"
            placeholder="数量"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
            style={{ width: '100px', marginBottom: 0 }}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#c9d1d9' }}>
            <input
              type="checkbox"
              checked={valuable}
              onChange={(e) => setValuable(e.target.checked)}
            />
            仅显示有价值的
          </label>
          <button className="button" onClick={handleSearch} disabled={isLoading || !repo.trim()}>
            <GitPullRequest size={18} style={{ marginRight: '8px' }} />
            搜索
          </button>
        </div>
      </div>

      {isLoading && <div className="loading">加载中...</div>}

      {error && (
        <div className="error">
          错误: {error?.response?.data?.detail || error?.message}
        </div>
      )}

      {data && (
        <>
          {!data.prs || data.prs.length === 0 ? (
            <div className="card">
              <p style={{ color: '#8b949e', textAlign: 'center', padding: '40px' }}>
                未找到 PR 数据。可能是：
                <br />
                1. 该仓库最近7天没有更新的 PR
                <br />
                2. 仓库名称格式不正确（应为 owner/repo，如：microsoft/vscode）
                <br />
                3. 仓库不存在或无权访问
                <br />
                4. GitHub API 访问受限
              </p>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '16px', color: '#8b949e', fontSize: '14px' }}>
                找到 {data.count} 个 PR {data.valuable ? '(有价值的)' : ''}
              </div>
              {data.prs.map((pr, idx) => {
                // Skip if PR has error
                if (pr.error) {
                  return (
                    <div key={idx} className="card" style={{ border: '1px solid #da3633' }}>
                      <p style={{ color: '#da3633' }}>错误: {pr.error}</p>
                    </div>
                  )
                }
                return (
                  <div key={idx} className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ marginBottom: '8px', color: '#58a6ff' }}>
                          <a
                            href={pr.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: '#58a6ff', textDecoration: 'none' }}
                          >
                            #{pr.number} {pr.title}
                            <ExternalLink size={14} style={{ marginLeft: '6px', display: 'inline' }} />
                          </a>
                        </h3>
                        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#8b949e', marginBottom: '8px' }}>
                          <span>作者: {pr.author}</span>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: pr.state === 'merged' ? '#238636' : pr.state === 'open' ? '#1f6feb' : '#da3633',
                            color: 'white',
                          }}>
                            {pr.state}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#8b949e' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <MessageSquare size={14} /> {pr.comments}
                          </span>
                          {pr.additions && pr.deletions && (
                            <span style={{ color: '#8b949e' }}>
                              +{pr.additions} / -{pr.deletions}
                            </span>
                          )}
                          {pr.value_score && (
                            <span style={{ color: '#f85149' }}>
                              价值评分: {pr.value_score}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {!data && !isLoading && !error && (
        <div className="card">
          <p style={{ color: '#8b949e', textAlign: 'center', padding: '40px' }}>
            请输入仓库名并点击搜索按钮
          </p>
        </div>
      )}
    </div>
  )
}

export default PRPage
