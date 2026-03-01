import React, { useState, useRef, useEffect } from 'react'
import { Github, X, ChevronDown, Search } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { githubAPI } from '../services/api'

export default function RepoSelector({ selectedRepo, onSelectRepo, onRemoveRepo }) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef(null)

  const {
    data: reposData,
    isLoading: reposLoading,
    refetch: refetchRepos,
    error: queryError,
  } = useQuery({
    queryKey: ['user-repos'],
    queryFn: () => githubAPI.getUserRepos(),
    enabled: showDropdown,
    staleTime: 1000 * 60 * 5,
    retry: false, // 不自动重试，避免重复请求
  })

  // 如果有查询错误，也显示
  const hasError = reposData?.error || queryError

  const repos = reposData?.repos || []
  const filteredRepos = repos.filter(repo =>
    repo.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (repo.description && repo.description.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false)
      }
    }

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showDropdown])

  return (
    <div className="chatbot-repo-selector" ref={dropdownRef}>
      <button
        type="button"
        className={`chatbot-repo-selector-btn ${selectedRepo ? 'has-repo' : ''}`}
        onClick={() => {
          setShowDropdown(!showDropdown)
          if (!showDropdown) {
            refetchRepos()
          }
        }}
      >
        {selectedRepo ? (
          <>
            <Github size={14} />
            <span className="chatbot-repo-selector-text">{selectedRepo}</span>
            <span
              className="chatbot-repo-selector-remove"
              onClick={(e) => {
                e.stopPropagation()
                e.preventDefault()
                onRemoveRepo()
              }}
              onMouseDown={(e) => {
                e.stopPropagation()
                e.preventDefault()
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.stopPropagation()
                  e.preventDefault()
                  onRemoveRepo()
                }
              }}
            >
              <X size={12} />
            </span>
          </>
        ) : (
          <>
            <Github size={14} />
            <span className="chatbot-repo-selector-text">All repositories</span>
            <ChevronDown size={14} className={showDropdown ? 'rotated' : ''} />
          </>
        )}
      </button>

      {showDropdown && (
        <div className="chatbot-repo-dropdown">
          <div className="chatbot-repo-search">
            <Search size={16} className="chatbot-repo-search-icon" />
            <input
              type="text"
              className="chatbot-repo-search-input"
              placeholder="搜索仓库..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          </div>
          {!reposLoading && !hasError && repos.length > 0 && (
            <div className="chatbot-repo-count">
              {searchQuery ? (
                <span>显示 {filteredRepos.length} / {repos.length} 个仓库</span>
              ) : (
                <span>共 {repos.length} 个仓库</span>
              )}
            </div>
          )}
                  <div className="chatbot-repo-list">
                    {reposLoading ? (
                      <div className="chatbot-repo-loading">加载中...</div>
                    ) : hasError ? (
                      <div className="chatbot-repo-error">
                        <div className="chatbot-repo-error-title">获取仓库失败</div>
                        <div className="chatbot-repo-error-message">
                          {reposData?.error || queryError?.message || '未知错误'}
                        </div>
                        <div className="chatbot-repo-error-hint">
                          请确保：
                          <br />1. 已登录 HubMind
                          <br />2. 在设置页面配置了有效的 GitHub Token
                          <br />3. Token 有 repo 权限
                        </div>
                      </div>
                    ) : filteredRepos.length === 0 ? (
                      <div className="chatbot-repo-empty">
                        {searchQuery ? '未找到匹配的仓库' : repos.length === 0 ? '暂无仓库' : '未找到匹配的仓库'}
                      </div>
                    ) : (
              filteredRepos.map((repo) => (
                <button
                  key={repo.id}
                  type="button"
                  className={`chatbot-repo-item ${selectedRepo === repo.full_name ? 'selected' : ''}`}
                  onClick={() => {
                    onSelectRepo(repo.full_name)
                    setShowDropdown(false)
                    setSearchQuery('')
                  }}
                >
                  <div className="chatbot-repo-item-header">
                    <Github size={14} className="chatbot-repo-item-icon" />
                    <span className="chatbot-repo-item-name">{repo.full_name}</span>
                    {repo.private && (
                      <span className="chatbot-repo-item-badge">Private</span>
                    )}
                  </div>
                  {repo.description && (
                    <div className="chatbot-repo-item-desc">{repo.description}</div>
                  )}
                  <div className="chatbot-repo-item-meta">
                    {repo.language && (
                      <span className="chatbot-repo-item-lang">{repo.language}</span>
                    )}
                    {repo.stargazers_count > 0 && (
                      <span className="chatbot-repo-item-stars">⭐ {repo.stargazers_count}</span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
