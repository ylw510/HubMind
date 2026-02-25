import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, Star, GitFork, ExternalLink } from 'lucide-react'
import { trendingAPI } from '../services/api'

function TrendingPage() {
  const [language, setLanguage] = useState('')
  const [since, setSince] = useState('daily')
  const [limit, setLimit] = useState(10)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['trending', language, since, limit],
    queryFn: () => trendingAPI.getTrending(language || null, since, limit),
    enabled: false,
  })

  const handleSearch = () => {
    refetch()
  }

  return (
    <div className="page-container">
      <h1 className="page-title">🔥 热门项目</h1>
      <p className="page-description">发现 GitHub 上最热门的项目</p>

      <div className="card">
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input"
            placeholder="编程语言 (如: python, javascript)"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}
          />
          <select
            className="input"
            value={since}
            onChange={(e) => setSince(e.target.value)}
            style={{ width: '150px', marginBottom: 0 }}
          >
            <option value="daily">今日</option>
            <option value="weekly">本周</option>
            <option value="monthly">本月</option>
          </select>
          <input
            type="number"
            className="input"
            placeholder="数量"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
            style={{ width: '100px', marginBottom: 0 }}
          />
          <button className="button" onClick={handleSearch} disabled={isLoading}>
            <TrendingUp size={18} style={{ marginRight: '8px' }} />
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
        <div>
          {data.repos?.map((repo, idx) => (
            <div key={idx} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ marginBottom: '8px', color: '#58a6ff' }}>
                    <a
                      href={repo.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#58a6ff', textDecoration: 'none' }}
                    >
                      {repo.name}
                      <ExternalLink size={14} style={{ marginLeft: '6px', display: 'inline' }} />
                    </a>
                  </h3>
                  <p style={{ color: '#8b949e', marginBottom: '12px', fontSize: '14px' }}>
                    {repo.description || '暂无描述'}
                  </p>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#8b949e' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Star size={14} /> {repo.stars}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <GitFork size={14} /> {repo.forks}
                    </span>
                    {repo.language && (
                      <span style={{ color: '#58a6ff' }}>● {repo.language}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TrendingPage
