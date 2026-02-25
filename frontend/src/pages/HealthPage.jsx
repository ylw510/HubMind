import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Heart, TrendingUp, Users, GitCommit } from 'lucide-react'
import { healthAPI } from '../services/api'

function HealthPage() {
  const [repo, setRepo] = useState('')
  const [days, setDays] = useState(30)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['health', repo, days],
    queryFn: () => healthAPI.getHealth(repo, days),
    enabled: false,
  })

  const handleSearch = () => {
    if (!repo.trim()) return
    refetch()
  }

  return (
    <div className="page-container">
      <h1 className="page-title">💚 仓库健康度</h1>
      <p className="page-description">分析仓库的健康指标和活跃度</p>

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
            placeholder="天数"
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value) || 30)}
            style={{ width: '100px', marginBottom: 0 }}
          />
          <button className="button" onClick={handleSearch} disabled={isLoading || !repo.trim()}>
            <Heart size={18} style={{ marginRight: '8px' }} />
            分析
          </button>
        </div>
      </div>

      {isLoading && <div className="loading">加载中...</div>}

      {error && (
        <div className="error">
          错误: {error?.response?.data?.detail || error?.message}
        </div>
      )}

      {data && !data.error && (
        <div>
          <div className="card">
            <h3 className="card-title">📊 健康指标</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <TrendingUp size={20} color="#238636" />
                  <span style={{ fontSize: '14px', color: '#8b949e' }}>PR 合并率</span>
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.pr_merge_rate}%
                </div>
              </div>
              <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Users size={20} color="#58a6ff" />
                  <span style={{ fontSize: '14px', color: '#8b949e' }}>活跃贡献者</span>
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.active_contributors}
                </div>
              </div>
              <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <GitCommit size={20} color="#f85149" />
                  <span style={{ fontSize: '14px', color: '#8b949e' }}>每日提交</span>
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.commits_per_day}
                </div>
              </div>
              <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Heart size={20} color="#da3633" />
                  <span style={{ fontSize: '14px', color: '#8b949e' }}>Issue 响应时间</span>
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.avg_issue_response_hours}h
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">📈 统计信息</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
              <div>
                <p style={{ color: '#8b949e', fontSize: '14px' }}>总提交数</p>
                <p style={{ fontSize: '20px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.total_commits}
                </p>
              </div>
              <div>
                <p style={{ color: '#8b949e', fontSize: '14px' }}>开放 Issue</p>
                <p style={{ fontSize: '20px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.open_issues}
                </p>
              </div>
              <div>
                <p style={{ color: '#8b949e', fontSize: '14px' }}>Stars</p>
                <p style={{ fontSize: '20px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.stars}
                </p>
              </div>
              <div>
                <p style={{ color: '#8b949e', fontSize: '14px' }}>Forks</p>
                <p style={{ fontSize: '20px', fontWeight: '600', color: '#f0f6fc' }}>
                  {data.forks}
                </p>
              </div>
            </div>
          </div>

          {data.contributor_list && data.contributor_list.length > 0 && (
            <div className="card">
              <h3 className="card-title">👥 活跃贡献者</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {data.contributor_list.slice(0, 10).map((contributor, idx) => (
                  <span
                    key={idx}
                    style={{
                      padding: '6px 12px',
                      background: '#1c2128',
                      borderRadius: '12px',
                      fontSize: '12px',
                      color: '#58a6ff',
                    }}
                  >
                    {contributor}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default HealthPage
