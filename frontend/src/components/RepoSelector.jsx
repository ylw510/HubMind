import React, { useState, useRef, useEffect } from 'react'
import { Github, X, ChevronDown, Search, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { githubAPI } from '../services/api'

export default function RepoSelector({ selectedRepo, onSelectRepo, onRemoveRepo }) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState('my') // 'my' or 'all'
  const [permissionCache, setPermissionCache] = useState({})
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const dropdownRef = useRef(null)
  const listRef = useRef(null)

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // 获取用户自己的仓库
  const {
    data: reposData,
    isLoading: reposLoading,
    refetch: refetchRepos,
    error: queryError,
  } = useQuery({
    queryKey: ['user-repos'],
    queryFn: () => githubAPI.getUserRepos(),
    enabled: showDropdown && searchMode === 'my',
    staleTime: 1000 * 60 * 5,
    retry: false,
  })

  // 搜索任意仓库
  const {
    data: searchData,
    isLoading: searchLoading,
    error: searchError,
  } = useQuery({
    queryKey: ['search-repos', debouncedSearchQuery],
    queryFn: () => githubAPI.searchRepos(debouncedSearchQuery, 20),
    enabled: showDropdown && searchMode === 'all' && debouncedSearchQuery.trim().length >= 2,
    staleTime: 1000 * 60 * 2,
    retry: false,
  })

  // 权限检查（当选择仓库时）
  const {
    data: permissionData,
    isLoading: permissionLoading,
  } = useQuery({
    queryKey: ['check-permission', selectedRepo],
    queryFn: () => githubAPI.checkIssuePermission(selectedRepo),
    enabled: !!selectedRepo && !permissionCache[selectedRepo],
    staleTime: 1000 * 60 * 10, // 10分钟缓存
    retry: false,
    onSuccess: (data) => {
      if (selectedRepo) {
        setPermissionCache(prev => ({ ...prev, [selectedRepo]: data }))
      }
    },
  })

  const hasError = reposData?.error || queryError
  const repos = searchMode === 'my' ? (reposData?.repos || []) : (searchData?.repos || [])
  const isLoading = searchMode === 'my' ? reposLoading : searchLoading
  const error = searchMode === 'my' ? hasError : searchError

  // 过滤我的仓库
  const filteredRepos = searchMode === 'my'
    ? repos.filter(repo =>
        repo.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (repo.description && repo.description.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : repos

  // 获取当前选中仓库的权限信息
  const currentPermission = selectedRepo
    ? (permissionCache[selectedRepo] || permissionData)
    : null

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false)
        setHighlightedIndex(-1)
      }
    }

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showDropdown])

  // 键盘导航处理
  useEffect(() => {
    if (!showDropdown) {
      setHighlightedIndex(-1)
      return
    }

    const handleKeyDown = (e) => {
      if (!showDropdown) return

      // 如果焦点在输入框或其他输入元素上，且不是导航键，则不处理
      const activeElement = document.activeElement
      const isInputFocused = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA'

      // 如果正在输入框中输入，只处理 Escape 键
      if (isInputFocused && e.key !== 'Escape' && e.key !== 'ArrowDown' && e.key !== 'ArrowUp' && e.key !== 'Enter') {
        return
      }

      const repos = filteredRepos
      if (repos.length === 0) return

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setHighlightedIndex(prev => {
            const next = prev < repos.length - 1 ? prev + 1 : 0
            // 滚动到可见区域
            scrollToItem(next)
            return next
          })
          break
        case 'ArrowUp':
          e.preventDefault()
          setHighlightedIndex(prev => {
            const next = prev > 0 ? prev - 1 : repos.length - 1
            // 滚动到可见区域
            scrollToItem(next)
            return next
          })
          break
        case 'Enter':
          e.preventDefault()
          if (highlightedIndex >= 0 && highlightedIndex < repos.length) {
            handleSelectRepo(repos[highlightedIndex].full_name)
          } else if (repos.length === 1) {
            // 如果只有一个结果，直接选择
            handleSelectRepo(repos[0].full_name)
          }
          break
        case 'Escape':
          e.preventDefault()
          setShowDropdown(false)
          setHighlightedIndex(-1)
          // 如果焦点在输入框，也清除搜索
          if (isInputFocused) {
            setSearchQuery('')
          }
          break
        default:
          // 其他按键不处理，让输入框正常输入
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [showDropdown, filteredRepos, highlightedIndex])

  // 滚动到指定项
  const scrollToItem = (index) => {
    if (!listRef.current) return
    const items = listRef.current.querySelectorAll('.chatbot-repo-item')
    if (items[index]) {
      items[index].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      })
    }
  }

  // 当仓库列表变化时，重置高亮
  useEffect(() => {
    if (filteredRepos.length > 0 && highlightedIndex >= filteredRepos.length) {
      setHighlightedIndex(-1)
    }
  }, [filteredRepos.length])

  const handleSelectRepo = async (repoFullName) => {
    onSelectRepo(repoFullName)
    setShowDropdown(false)
    setSearchQuery('')
    setHighlightedIndex(-1)
    // 如果权限信息不在缓存中，会在useQuery中自动获取
  }

  return (
    <div className="chatbot-repo-selector" ref={dropdownRef}>
      <button
        type="button"
        className={`chatbot-repo-selector-btn ${selectedRepo ? 'has-repo' : ''}`}
        onClick={() => {
          setShowDropdown(!showDropdown)
          if (!showDropdown && searchMode === 'my') {
            refetchRepos()
          }
        }}
      >
        {selectedRepo ? (
          <>
            <Github size={14} />
            <span className="chatbot-repo-selector-text">{selectedRepo}</span>
            {currentPermission && (
              <span
                className={`chatbot-repo-permission-indicator ${
                  currentPermission.can_create ? 'can-create' : 'cannot-create'
                }`}
                title={currentPermission.message}
              >
                {currentPermission.can_create ? (
                  <CheckCircle2 size={12} />
                ) : (
                  <AlertCircle size={12} />
                )}
              </span>
            )}
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
          {/* 模式切换 */}
          <div className="chatbot-repo-mode-switch">
            <button
              type="button"
              className={`chatbot-repo-mode-btn ${searchMode === 'my' ? 'active' : ''}`}
              onClick={() => {
                setSearchMode('my')
                setSearchQuery('')
              }}
            >
              我的仓库
            </button>
            <button
              type="button"
              className={`chatbot-repo-mode-btn ${searchMode === 'all' ? 'active' : ''}`}
              onClick={() => {
                setSearchMode('all')
                setSearchQuery('')
              }}
            >
              搜索任意仓库
            </button>
          </div>

          {/* 搜索框 */}
          <div className="chatbot-repo-search">
            <Search size={16} className="chatbot-repo-search-icon" />
            <input
              type="text"
              className="chatbot-repo-search-input"
              placeholder={searchMode === 'my' ? '搜索我的仓库...' : '输入仓库名或搜索词（如：facebook/react）'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            {searchMode === 'all' && searchLoading && (
              <Loader2 size={16} className="chatbot-repo-search-loading" />
            )}
          </div>

          {/* 统计信息 */}
          {!isLoading && !error && repos.length > 0 && (
            <div className="chatbot-repo-count">
              {searchMode === 'my' ? (
                searchQuery ? (
                  <span>显示 {filteredRepos.length} / {repos.length} 个仓库</span>
                ) : (
                  <span>共 {repos.length} 个仓库</span>
                )
              ) : (
                <span>找到 {repos.length} 个仓库</span>
              )}
            </div>
          )}

          {/* 权限提示 */}
          {selectedRepo && currentPermission && (
            <div className={`chatbot-repo-permission-hint ${currentPermission.can_create ? 'success' : 'warning'}`}>
              {currentPermission.can_create ? (
                <CheckCircle2 size={14} />
              ) : (
                <AlertCircle size={14} />
              )}
              <span>{currentPermission.message}</span>
            </div>
          )}

          {/* 仓库列表 */}
          <div className="chatbot-repo-list" ref={listRef}>
            {isLoading ? (
              <div className="chatbot-repo-loading">
                <Loader2 size={16} className="spin" />
                <span>加载中...</span>
              </div>
            ) : error ? (
              <div className="chatbot-repo-error">
                <div className="chatbot-repo-error-title">获取仓库失败</div>
                <div className="chatbot-repo-error-message">
                  {reposData?.error || queryError?.message || searchError?.message || '未知错误'}
                </div>
                {searchMode === 'my' && (
                  <div className="chatbot-repo-error-hint">
                    请确保：
                    <br />1. 已登录 HubMind
                    <br />2. 在设置页面配置了有效的 GitHub Token
                    <br />3. Token 有 repo 权限
                  </div>
                )}
              </div>
            ) : searchMode === 'all' && searchQuery.trim().length < 2 ? (
              <div className="chatbot-repo-empty">
                请输入至少2个字符进行搜索
              </div>
            ) : filteredRepos.length === 0 ? (
              <div className="chatbot-repo-empty">
                {searchMode === 'my'
                  ? (searchQuery ? '未找到匹配的仓库' : repos.length === 0 ? '暂无仓库' : '未找到匹配的仓库')
                  : '未找到匹配的仓库'}
              </div>
            ) : (
              filteredRepos.map((repo, index) => {
                const repoPermission = permissionCache[repo.full_name]
                const isHighlighted = index === highlightedIndex
                return (
                  <button
                    key={repo.id || repo.full_name}
                    type="button"
                    className={`chatbot-repo-item ${selectedRepo === repo.full_name ? 'selected' : ''} ${isHighlighted ? 'highlighted' : ''}`}
                    onClick={() => handleSelectRepo(repo.full_name)}
                    onMouseEnter={() => setHighlightedIndex(index)}
                  >
                    <div className="chatbot-repo-item-header">
                      <Github size={14} className="chatbot-repo-item-icon" />
                      <span className="chatbot-repo-item-name">{repo.full_name}</span>
                      {repo.private && (
                        <span className="chatbot-repo-item-badge">Private</span>
                      )}
                      {repoPermission && (
                        <span
                          className={`chatbot-repo-item-permission ${
                            repoPermission.can_create ? 'can-create' : 'cannot-create'
                          }`}
                          title={repoPermission.message}
                        >
                          {repoPermission.can_create ? (
                            <CheckCircle2 size={12} />
                          ) : (
                            <AlertCircle size={12} />
                          )}
                        </span>
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
                      {repo.forks_count > 0 && (
                        <span className="chatbot-repo-item-forks">🍴 {repo.forks_count}</span>
                      )}
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
