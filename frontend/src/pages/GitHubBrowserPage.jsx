import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Github, FileText, Code, GitBranch, Star, Eye, GitFork, ExternalLink, Folder, File } from 'lucide-react'
import { githubAPI } from '../services/api'
import ReactMarkdown from 'react-markdown'

function GitHubBrowserPage() {
  const [repo, setRepo] = useState('')
  const [path, setPath] = useState('')
  const [viewMode, setViewMode] = useState('info') // info, files, readme

  const { data: repoInfo, isLoading: loadingInfo, error: errorInfo, refetch: refetchInfo } = useQuery({
    queryKey: ['repo-info', repo],
    queryFn: () => githubAPI.getRepoInfo(repo),
    enabled: false,
  })

  const { data: repoFiles, isLoading: loadingFiles, error: errorFiles, refetch: refetchFiles } = useQuery({
    queryKey: ['repo-files', repo, path],
    queryFn: () => githubAPI.getRepoFiles(repo, path),
    enabled: false,
  })

  const { data: readme, isLoading: loadingReadme, error: errorReadme, refetch: refetchReadme } = useQuery({
    queryKey: ['repo-readme', repo],
    queryFn: () => githubAPI.getReadme(repo),
    enabled: false,
  })

  const handleSearch = () => {
    if (!repo.trim()) {
      alert('请输入仓库名（格式：owner/repo）')
      return
    }
    if (!repo.includes('/')) {
      alert('仓库名格式不正确，应为：owner/repo（如：microsoft/vscode）')
      return
    }
    refetchInfo()
    if (viewMode === 'readme') {
      refetchReadme()
    } else if (viewMode === 'files') {
      refetchFiles()
    }
  }

  const handlePathClick = (newPath) => {
    setPath(newPath)
    if (viewMode === 'files') {
      refetchFiles()
    }
  }

  const handleViewModeChange = (mode) => {
    setViewMode(mode)
    if (mode === 'readme' && repo) {
      refetchReadme()
    } else if (mode === 'files' && repo) {
      refetchFiles()
    }
  }

  return (
    <div className="page-container">
      <h1 className="page-title">🔍 GitHub 浏览器</h1>
      <p className="page-description">浏览 GitHub 仓库、查看代码和文件</p>

      <div className="card">
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input"
            placeholder="仓库名 (如: microsoft/vscode)"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            style={{ flex: 1, minWidth: '200px', marginBottom: 0 }}
          />
          <button className="button" onClick={handleSearch} disabled={loadingInfo || !repo.trim()}>
            <Github size={18} style={{ marginRight: '8px' }} />
            浏览
          </button>
        </div>
      </div>

      {loadingInfo && <div className="loading">加载中...</div>}

      {errorInfo && (
        <div className="error">
          错误: {errorInfo?.response?.data?.detail || errorInfo?.message}
        </div>
      )}

      {repoInfo && !errorInfo && (
        <div>
          {/* 仓库信息卡片 */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
              <div style={{ flex: 1 }}>
                <h2 style={{ marginBottom: '8px', color: '#58a6ff' }}>
                  <a
                    href={repoInfo.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#58a6ff', textDecoration: 'none' }}
                  >
                    {repoInfo.full_name}
                    <ExternalLink size={16} style={{ marginLeft: '8px', display: 'inline' }} />
                  </a>
                </h2>
                {repoInfo.description && (
                  <p style={{ color: '#8b949e', marginBottom: '12px' }}>{repoInfo.description}</p>
                )}
                <div style={{ display: 'flex', gap: '16px', fontSize: '14px', color: '#8b949e', flexWrap: 'wrap' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Star size={16} /> {repoInfo.stargazers_count?.toLocaleString() || 0}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <GitFork size={16} /> {repoInfo.forks_count?.toLocaleString() || 0}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Eye size={16} /> {repoInfo.watchers_count?.toLocaleString() || 0}
                  </span>
                  {repoInfo.language && (
                    <span style={{ color: '#58a6ff' }}>● {repoInfo.language}</span>
                  )}
                  <span>更新于 {new Date(repoInfo.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* 视图切换按钮 */}
            <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid #30363d', paddingTop: '16px' }}>
              <button
                className={`button ${viewMode === 'info' ? '' : 'button-secondary'}`}
                onClick={() => handleViewModeChange('info')}
                style={{ flex: 1 }}
              >
                <FileText size={16} style={{ marginRight: '8px' }} />
                仓库信息
              </button>
              <button
                className={`button ${viewMode === 'files' ? '' : 'button-secondary'}`}
                onClick={() => handleViewModeChange('files')}
                style={{ flex: 1 }}
              >
                <Folder size={16} style={{ marginRight: '8px' }} />
                文件浏览
              </button>
              <button
                className={`button ${viewMode === 'readme' ? '' : 'button-secondary'}`}
                onClick={() => handleViewModeChange('readme')}
                style={{ flex: 1 }}
              >
                <Code size={16} style={{ marginRight: '8px' }} />
                README
              </button>
            </div>
          </div>

          {/* 仓库信息视图 */}
          {viewMode === 'info' && (
            <div className="card">
              <h3 className="card-title">📊 仓库统计</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                  <div style={{ fontSize: '14px', color: '#8b949e', marginBottom: '8px' }}>Stars</div>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                    {repoInfo.stargazers_count?.toLocaleString() || 0}
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                  <div style={{ fontSize: '14px', color: '#8b949e', marginBottom: '8px' }}>Forks</div>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                    {repoInfo.forks_count?.toLocaleString() || 0}
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                  <div style={{ fontSize: '14px', color: '#8b949e', marginBottom: '8px' }}>Watchers</div>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                    {repoInfo.watchers_count?.toLocaleString() || 0}
                  </div>
                </div>
                <div style={{ padding: '16px', background: '#1c2128', borderRadius: '6px' }}>
                  <div style={{ fontSize: '14px', color: '#8b949e', marginBottom: '8px' }}>Open Issues</div>
                  <div style={{ fontSize: '24px', fontWeight: '600', color: '#f0f6fc' }}>
                    {repoInfo.open_issues_count?.toLocaleString() || 0}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '20px' }}>
                <h4 style={{ color: '#f0f6fc', marginBottom: '12px' }}>仓库信息</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', fontSize: '14px' }}>
                  <div>
                    <span style={{ color: '#8b949e' }}>默认分支:</span>
                    <span style={{ color: '#f0f6fc', marginLeft: '8px' }}>{repoInfo.default_branch}</span>
                  </div>
                  <div>
                    <span style={{ color: '#8b949e' }}>大小:</span>
                    <span style={{ color: '#f0f6fc', marginLeft: '8px' }}>
                      {(repoInfo.size / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#8b949e' }}>创建时间:</span>
                    <span style={{ color: '#f0f6fc', marginLeft: '8px' }}>
                      {new Date(repoInfo.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#8b949e' }}>许可证:</span>
                    <span style={{ color: '#f0f6fc', marginLeft: '8px' }}>
                      {repoInfo.license?.name || '无'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 文件浏览视图 */}
          {viewMode === 'files' && (
            <div className="card">
              <h3 className="card-title">📁 文件浏览</h3>
              {path && (
                <div style={{ marginBottom: '16px' }}>
                  <button
                    className="button button-secondary"
                    onClick={() => handlePathClick('')}
                    style={{ fontSize: '12px' }}
                  >
                    ← 返回根目录
                  </button>
                  <span style={{ color: '#8b949e', marginLeft: '12px' }}>当前路径: {path}</span>
                </div>
              )}
              {loadingFiles && <div className="loading">加载文件列表中...</div>}
              {errorFiles && (
                <div className="error">
                  错误: {errorFiles?.response?.data?.detail || errorFiles?.message}
                </div>
              )}
              {repoFiles && !errorFiles && (
                <div>
                  {repoFiles.length === 0 ? (
                    <p style={{ color: '#8b949e', textAlign: 'center', padding: '40px' }}>
                      此目录为空
                    </p>
                  ) : (
                    <div>
                      {repoFiles.map((file, idx) => (
                        <div
                          key={idx}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            padding: '12px',
                            borderBottom: '1px solid #30363d',
                            cursor: file.type === 'dir' ? 'pointer' : 'default',
                          }}
                          onClick={() => file.type === 'dir' && handlePathClick(file.path)}
                        >
                          {file.type === 'dir' ? (
                            <Folder size={20} color="#58a6ff" />
                          ) : (
                            <File size={20} color="#8b949e" />
                          )}
                          <span style={{ flex: 1, color: '#f0f6fc' }}>{file.name}</span>
                          {file.size && (
                            <span style={{ color: '#8b949e', fontSize: '12px' }}>
                              {(file.size / 1024).toFixed(1)} KB
                            </span>
                          )}
                          {file.type === 'file' && (
                            <a
                              href={file.html_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <ExternalLink size={16} color="#58a6ff" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* README 视图 */}
          {viewMode === 'readme' && (
            <div className="card">
              <h3 className="card-title">📖 README</h3>
              {loadingReadme && <div className="loading">加载 README...</div>}
              {errorReadme && (
                <div className="error">
                  错误: {errorReadme?.response?.data?.detail || errorReadme?.message}
                </div>
              )}
              {readme && !errorReadme && (
                <div style={{ padding: '20px', background: '#0d1117', borderRadius: '6px' }}>
                  <ReactMarkdown>{readme.content}</ReactMarkdown>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!repoInfo && !loadingInfo && !errorInfo && (
        <div className="card">
          <p style={{ color: '#8b949e', textAlign: 'center', padding: '40px' }}>
            请输入仓库名并点击浏览按钮
          </p>
        </div>
      )}
    </div>
  )
}

export default GitHubBrowserPage
