import React, { useState, useEffect } from 'react'
import { X, Tag, User, AlertCircle, CheckCircle, Send, Loader } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { issueAPI } from '../services/api'

export default function IssuePanel({ repo, initialText, onClose, onIssueCreated }) {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [selectedLabels, setSelectedLabels] = useState([])
  const [selectedAssignees, setSelectedAssignees] = useState([])
  const [showLabelsDropdown, setShowLabelsDropdown] = useState(false)
  const [showAssigneesDropdown, setShowAssigneesDropdown] = useState(false)

  // 解析初始文本
  const {
    data: parsedData,
    isLoading: parsing,
    error: parseError,
  } = useQuery({
    queryKey: ['parse-issue', repo, initialText],
    queryFn: () => {
      if (!repo || !initialText || initialText.trim() === '') {
        throw new Error('Repository and text are required')
      }
      return issueAPI.parseIssue(repo, initialText)
    },
    enabled: !!repo && !!initialText && initialText.trim() !== '',
    staleTime: 0, // 每次都重新解析
    retry: 2,
  })

  // 获取仓库标签
  const {
    data: labelsData,
    isLoading: labelsLoading,
  } = useQuery({
    queryKey: ['repo-labels', repo],
    queryFn: () => issueAPI.getRepoLabels(repo),
    enabled: !!repo,
    staleTime: 1000 * 60 * 5,
  })

  // 获取协作者
  const {
    data: collaboratorsData,
    isLoading: collaboratorsLoading,
  } = useQuery({
    queryKey: ['repo-collaborators', repo],
    queryFn: () => issueAPI.getRepoCollaborators(repo),
    enabled: !!repo,
    staleTime: 1000 * 60 * 5,
  })

  // 当解析完成时，更新表单
  useEffect(() => {
    if (parsedData && parsedData.title && parsedData.body) {
      // 强制更新标题和描述（首次加载或内容变化时）
      setTitle(parsedData.title)
      setBody(parsedData.body)

      // 标签可以自动更新（合并，不覆盖）
      if (parsedData.suggested_labels && parsedData.suggested_labels.length > 0) {
        setSelectedLabels(prev => {
          // 合并新建议的标签，不覆盖已选择的
          const newLabels = [...new Set([...prev, ...parsedData.suggested_labels])]
          return newLabels
        })
      }
    }
  }, [parsedData])

  // 当 initialText 变化时，重置表单并等待解析
  useEffect(() => {
    if (initialText && repo) {
      // 重置表单，等待解析完成
      setTitle('')
      setBody('')
      setSelectedLabels([])
    }
  }, [initialText, repo])

  // 创建 issue
  const createMutation = useMutation({
    mutationFn: () => issueAPI.createIssueDraft(
      repo,
      title,
      body,
      selectedAssignees.length > 0 ? selectedAssignees : null,
      selectedLabels.length > 0 ? selectedLabels : null
    ),
    onSuccess: (data) => {
      onIssueCreated?.(data)
      onClose()
    },
  })

  const labels = labelsData?.labels || []
  const collaborators = collaboratorsData?.collaborators || []
  const similarIssues = parsedData?.similar_issues || []

  const handleToggleLabel = (labelName) => {
    setSelectedLabels(prev =>
      prev.includes(labelName)
        ? prev.filter(l => l !== labelName)
        : [...prev, labelName]
    )
  }

  const handleToggleAssignee = (username) => {
    setSelectedAssignees(prev =>
      prev.includes(username)
        ? prev.filter(a => a !== username)
        : [...prev, username]
    )
  }

  const handleSubmit = () => {
    if (!title.trim()) {
      alert('请输入 Issue 标题')
      return
    }
    createMutation.mutate()
  }

  return (
    <div className="issue-panel">
      <div className="issue-panel-header">
        <div className="issue-panel-header-content">
          <h3 className="issue-panel-title">New Issue</h3>
          <div className="issue-panel-repo">{repo}</div>
        </div>
        <button
          type="button"
          className="issue-panel-close"
          onClick={onClose}
          title="关闭"
        >
          <X size={18} />
        </button>
      </div>

      <div className="issue-panel-content">
        {parsing && (
          <div className="issue-panel-loading">
            <Loader size={16} className="spin" />
            <span>正在解析 Issue 内容...</span>
          </div>
        )}

        {parseError && (
          <div className="issue-panel-error" style={{ padding: '12px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', marginBottom: '16px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={14} />
            <span>解析失败: {parseError.message || '未知错误'}</span>
          </div>
        )}

        {similarIssues.length > 0 && (
          <div className="issue-panel-similar">
            <div className="issue-panel-similar-header">
              <AlertCircle size={14} />
              <span>发现 {similarIssues.length} 个相似 Issue</span>
            </div>
            <div className="issue-panel-similar-list">
              {similarIssues.slice(0, 3).map((issue, idx) => (
                <a
                  key={idx}
                  href={issue.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="issue-panel-similar-item"
                >
                  #{issue.number} {issue.title}
                </a>
              ))}
            </div>
          </div>
        )}

        <div className="issue-panel-form">
          <div className="issue-panel-field">
            <label className="issue-panel-label">Title</label>
            <input
              type="text"
              className="issue-panel-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Issue title"
            />
          </div>

          <div className="issue-panel-field">
            <label className="issue-panel-label">Description</label>
            <textarea
              className="issue-panel-textarea"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Issue description (Markdown supported)"
              rows={12}
            />
          </div>

          <div className="issue-panel-field">
            <label className="issue-panel-label">Labels</label>
            <div className="issue-panel-selector">
              <button
                type="button"
                className="issue-panel-selector-btn"
                onClick={() => setShowLabelsDropdown(!showLabelsDropdown)}
              >
                <Tag size={14} />
                <span>
                  {selectedLabels.length > 0
                    ? `${selectedLabels.length} labels selected`
                    : 'Add labels'}
                </span>
              </button>
              {showLabelsDropdown && (
                <div className="issue-panel-dropdown">
                  {labelsLoading ? (
                    <div className="issue-panel-dropdown-loading">加载中...</div>
                  ) : labels.length === 0 ? (
                    <div className="issue-panel-dropdown-empty">暂无标签</div>
                  ) : (
                    labels.map((label) => (
                      <label
                        key={label.name}
                        className="issue-panel-dropdown-item"
                      >
                        <input
                          type="checkbox"
                          checked={selectedLabels.includes(label.name)}
                          onChange={() => handleToggleLabel(label.name)}
                        />
                        <span
                          className="issue-panel-label-badge"
                          style={{ backgroundColor: `#${label.color}` }}
                        >
                          {label.name}
                        </span>
                        {label.description && (
                          <span className="issue-panel-label-desc">{label.description}</span>
                        )}
                      </label>
                    ))
                  )}
                </div>
              )}
              {selectedLabels.length > 0 && (
                <div className="issue-panel-selected">
                  {selectedLabels.map((labelName) => {
                    const label = labels.find(l => l.name === labelName)
                    return (
                      <span
                        key={labelName}
                        className="issue-panel-selected-badge"
                        style={{ backgroundColor: label ? `#${label.color}` : '#6d6d6d' }}
                      >
                        {labelName}
                        <button
                          type="button"
                          className="issue-panel-selected-remove"
                          onClick={() => handleToggleLabel(labelName)}
                        >
                          <X size={12} />
                        </button>
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="issue-panel-field">
            <label className="issue-panel-label">Assignees</label>
            <div className="issue-panel-selector">
              <button
                type="button"
                className="issue-panel-selector-btn"
                onClick={() => setShowAssigneesDropdown(!showAssigneesDropdown)}
              >
                <User size={14} />
                <span>
                  {selectedAssignees.length > 0
                    ? `${selectedAssignees.length} assignees`
                    : 'Assign to someone'}
                </span>
              </button>
              {showAssigneesDropdown && (
                <div className="issue-panel-dropdown">
                  {collaboratorsLoading ? (
                    <div className="issue-panel-dropdown-loading">加载中...</div>
                  ) : collaborators.length === 0 ? (
                    <div className="issue-panel-dropdown-empty">暂无协作者</div>
                  ) : (
                    collaborators.map((collab) => (
                      <label
                        key={collab.login}
                        className="issue-panel-dropdown-item"
                      >
                        <input
                          type="checkbox"
                          checked={selectedAssignees.includes(collab.login)}
                          onChange={() => handleToggleAssignee(collab.login)}
                        />
                        <img
                          src={collab.avatar_url}
                          alt={collab.login}
                          className="issue-panel-avatar"
                        />
                        <span>{collab.login}</span>
                      </label>
                    ))
                  )}
                </div>
              )}
              {selectedAssignees.length > 0 && (
                <div className="issue-panel-selected">
                  {selectedAssignees.map((username) => {
                    const collab = collaborators.find(c => c.login === username)
                    return (
                      <span key={username} className="issue-panel-selected-badge">
                        {collab && (
                          <img
                            src={collab.avatar_url}
                            alt={username}
                            className="issue-panel-selected-avatar"
                          />
                        )}
                        {username}
                        <button
                          type="button"
                          className="issue-panel-selected-remove"
                          onClick={() => handleToggleAssignee(username)}
                        >
                          <X size={12} />
                        </button>
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="issue-panel-footer">
        <button
          type="button"
          className="issue-panel-cancel"
          onClick={onClose}
        >
          Cancel
        </button>
        <button
          type="button"
          className="issue-panel-submit"
          onClick={handleSubmit}
          disabled={!title.trim() || createMutation.isPending}
        >
          {createMutation.isPending ? (
            <>
              <Loader size={14} className="spin" />
              <span>Creating...</span>
            </>
          ) : (
            <>
              <Send size={14} />
              <span>Submit new issue</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
