import React, { useState, useRef, useCallback, useEffect } from 'react'
import { X, CheckCircle, Loader, ExternalLink, GripVertical } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { githubAPI, prAPI } from '../services/api'

const STEP = { CONFIRM_REPO: 'confirm_repo', SHOW_PRS: 'show_prs' }
const MIN_WIDTH = 320
const MAX_WIDTH = 900
const DEFAULT_WIDTH = 440
const TITLE_TRUNCATE = 50

const DEFAULT_COLUMN_WIDTHS = [52, 220, 90, 72, 40]
const MIN_COLUMN_WIDTHS = [40, 80, 60, 56, 36]

function getDefaultPosition() {
  if (typeof window === 'undefined') return { x: 400, y: 80 }
  return {
    x: Math.max(20, window.innerWidth - DEFAULT_WIDTH - 20),
    y: 80,
  }
}

export default function PRPanel({ initialQuery, onClose }) {
  const [step, setStep] = useState(STEP.CONFIRM_REPO)
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [panelWidth, setPanelWidth] = useState(DEFAULT_WIDTH)
  const [panelPosition, setPanelPosition] = useState(getDefaultPosition)
  const [isDragging, setIsDragging] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [tooltip, setTooltip] = useState({ show: false, text: '', x: 0, y: 0 })
  const [columnWidths, setColumnWidths] = useState(DEFAULT_COLUMN_WIDTHS)
  const [resizingCol, setResizingCol] = useState(null)
  const [authorFilter, setAuthorFilter] = useState('')
  const tooltipTimerRef = useRef(null)
  const dragStartRef = useRef({ x: 0, y: 0, panelX: 0, panelY: 0 })
  const resizeStartRef = useRef({ x: 0, width: 0 })
  const colResizeStartRef = useRef({ x: 0, widths: [] })

  const {
    data: searchData,
    isLoading: searchLoading,
    error: searchError,
  } = useQuery({
    queryKey: ['search-repos-pr-panel', initialQuery],
    queryFn: () => githubAPI.searchRepos(initialQuery, 5),
    enabled: !!initialQuery && step === STEP.CONFIRM_REPO,
    staleTime: 1000 * 60,
  })

  const repos = searchData?.repos || []
  const authorQuery = authorFilter.trim() || null
  const {
    data: prsData,
    isLoading: prsLoading,
    error: prsError,
  } = useQuery({
    queryKey: ['prs-today', selectedRepo, authorQuery],
    queryFn: () => prAPI.getPRs(selectedRepo, 20, false, authorQuery),
    enabled: !!selectedRepo && step === STEP.SHOW_PRS,
    staleTime: 1000 * 60,
  })

  const prs = prsData?.prs || []

  const handleConfirmRepo = (repo) => {
    setSelectedRepo(repo.full_name)
    setStep(STEP.SHOW_PRS)
  }

  const handleBackToConfirm = () => {
    setSelectedRepo(null)
    setAuthorFilter('')
    setStep(STEP.CONFIRM_REPO)
  }

  const handleHeaderMouseDown = useCallback((e) => {
    if (e.button !== 0 || e.target.closest('button')) return
    setIsDragging(true)
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      panelX: panelPosition.x,
      panelY: panelPosition.y,
    }
  }, [panelPosition.x, panelPosition.y])

  const handleResizeMouseDown = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.button !== 0) return
    setIsResizing(true)
    resizeStartRef.current = { x: e.clientX, width: panelWidth }
  }, [panelWidth])

  useEffect(() => {
    if (resizingCol !== null) {
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      return () => {
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }
    }
  }, [resizingCol])

  useEffect(() => {
    if (!isDragging && !isResizing && resizingCol === null) return
    const onMove = (e) => {
      if (isDragging) {
        const dx = e.clientX - dragStartRef.current.x
        const dy = e.clientY - dragStartRef.current.y
        setPanelPosition({
          x: Math.max(0, Math.min(window.innerWidth - 200, dragStartRef.current.panelX + dx)),
          y: Math.max(0, Math.min(window.innerHeight - 120, dragStartRef.current.panelY + dy)),
        })
      }
      if (isResizing) {
        const dx = e.clientX - resizeStartRef.current.x
        const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, resizeStartRef.current.width + dx))
        setPanelWidth(newWidth)
      }
      if (resizingCol !== null) {
        const { x, widths } = colResizeStartRef.current
        const delta = e.clientX - x
        const i = resizingCol
        const nextWidth = widths[i] + delta
        const nextNextWidth = widths[i + 1] - delta
        const clampedCur = Math.min(
          Math.max(MIN_COLUMN_WIDTHS[i], nextWidth),
          widths[i] + widths[i + 1] - MIN_COLUMN_WIDTHS[i + 1]
        )
        const clampedNext = widths[i] + widths[i + 1] - clampedCur
        setColumnWidths((prev) => {
          const next = [...prev]
          next[i] = clampedCur
          next[i + 1] = clampedNext
          return next
        })
      }
    }
    const onUp = () => {
      setIsDragging(false)
      setIsResizing(false)
      setResizingCol(null)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [isDragging, isResizing, resizingCol])

  const showTitleTooltip = useCallback((e, title) => {
    if (!title || title.length <= TITLE_TRUNCATE) return
    if (tooltipTimerRef.current) clearTimeout(tooltipTimerRef.current)
    tooltipTimerRef.current = setTimeout(() => {
      const rect = e.currentTarget.getBoundingClientRect()
      setTooltip({ show: true, text: title, x: rect.left + rect.width / 2, y: rect.top })
    }, 400)
  }, [])

  const hideTitleTooltip = useCallback(() => {
    if (tooltipTimerRef.current) {
      clearTimeout(tooltipTimerRef.current)
      tooltipTimerRef.current = null
    }
    setTooltip(s => ({ ...s, show: false }))
  }, [])

  const handleColResizeStart = useCallback((e, colIndex) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.button !== 0) return
    setResizingCol(colIndex)
    colResizeStartRef.current = { x: e.clientX, widths: columnWidths }
  }, [columnWidths])

  const panelStyle = {
    width: panelWidth,
    left: panelPosition.x,
    top: panelPosition.y,
    height: 'calc(100vh - 80px)',
    maxHeight: 'calc(100vh - 80px)',
  }

  return (
    <>
      <div
        className={`pr-panel ${isDragging ? 'pr-panel-dragging' : ''} ${isResizing ? 'pr-panel-resizing' : ''}`}
        style={panelStyle}
      >
        <header
          className="pr-panel-header"
          onMouseDown={handleHeaderMouseDown}
        >
          <div className="pr-panel-header-drag-hint">
            <GripVertical size={14} />
          </div>
          <div className="pr-panel-header-content">
            <h3 className="pr-panel-title">
              {step === STEP.CONFIRM_REPO ? '确认项目' : '今日 PR'}
            </h3>
            <div className="pr-panel-repo">
              {step === STEP.SHOW_PRS ? selectedRepo : initialQuery ? `搜索: ${initialQuery}` : ''}
            </div>
          </div>
          <button
            type="button"
            className="pr-panel-close"
            onClick={onClose}
            title="关闭"
          >
            <X size={18} />
          </button>
        </header>

        <div className="pr-panel-content">
          {step === STEP.CONFIRM_REPO && (
            <>
              <p className="pr-panel-workflow-desc">
                工作流：先确认查到的项目是否是您要查看的仓库，确认后再加载今日 PR 列表。
              </p>
              {searchLoading && (
                <div className="pr-panel-loading">
                  <Loader size={20} className="spin" />
                  <span>正在查找项目...</span>
                </div>
              )}
              {searchError && (
                <div className="pr-panel-error">
                  <span>查找失败: {searchError.message || '请检查网络或 GitHub Token'}</span>
                </div>
              )}
              {!searchLoading && !searchError && repos.length === 0 && (
                <div className="pr-panel-empty">未找到匹配的仓库，请换一个关键词试试。</div>
              )}
              {!searchLoading && !searchError && repos.length > 0 && (
                <div className="pr-panel-confirm">
                  <p className="pr-panel-confirm-question">找到以下项目，是否要查看该仓库的今日 PR？</p>
                  <div className="pr-panel-repo-list">
                    {repos.map((repo) => (
                      <div key={repo.id} className="pr-panel-repo-card">
                        <div className="pr-panel-repo-name">
                          <a
                            href={repo.html_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="pr-panel-repo-link"
                          >
                            {repo.full_name}
                            <ExternalLink size={12} />
                          </a>
                        </div>
                        {repo.description && (
                          <p className="pr-panel-repo-desc">{repo.description}</p>
                        )}
                        <div className="pr-panel-repo-meta">
                          {repo.language && <span>{repo.language}</span>}
                          <span>⭐ {repo.stargazers_count}</span>
                        </div>
                        <button
                          type="button"
                          className="pr-panel-btn-confirm"
                          onClick={() => handleConfirmRepo(repo)}
                        >
                          <CheckCircle size={14} />
                          是，查看此项目的今日 PR
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {step === STEP.SHOW_PRS && (
            <>
              <button
                type="button"
                className="pr-panel-back"
                onClick={handleBackToConfirm}
              >
                ← 重新选择项目
              </button>
              <div className="pr-panel-author-filter">
                <label className="pr-panel-author-label">按作者筛选</label>
                <input
                  type="text"
                  className="pr-panel-author-input"
                  placeholder="输入 GitHub 用户名"
                  value={authorFilter}
                  onChange={(e) => setAuthorFilter(e.target.value)}
                  title="输入作者 GitHub 用户名可只显示该用户的 PR"
                />
                {authorFilter.trim() && (
                  <button
                    type="button"
                    className="pr-panel-author-clear"
                    onClick={() => setAuthorFilter('')}
                    title="清除作者筛选"
                  >
                    清除
                  </button>
                )}
              </div>
              {prsLoading && (
                <div className="pr-panel-loading">
                  <Loader size={20} className="spin" />
                  <span>{authorQuery ? `正在加载 ${authorQuery} 的 PR...` : '正在加载今日 PR...'}</span>
                </div>
              )}
              {prsError && (
                <div className="pr-panel-error">
                  <span>加载 PR 失败: {prsError.message || '未知错误'}</span>
                </div>
              )}
              {!prsLoading && !prsError && prs.length === 0 && (
                <div className="pr-panel-empty">
                  {authorQuery
                    ? `该仓库中未找到用户 ${authorQuery} 的 PR。`
                    : '该仓库今日暂无 PR 或列表为空。'}
                </div>
              )}
              {!prsLoading && !prsError && prs.length > 0 && (
                <div className="pr-panel-table-wrap">
                  <table className="pr-panel-table">
                    <colgroup>
                      {columnWidths.map((w, i) => (
                        <col key={i} style={{ width: w + 'px' }} />
                      ))}
                    </colgroup>
                    <thead>
                      <tr>
                        {['#', '标题', '作者', '状态', ''].map((label, i) => (
                          <th key={i} style={{ width: columnWidths[i] + 'px' }}>
                            {label}
                            {i < columnWidths.length - 1 && (
                              <div
                                className="pr-panel-col-resize-handle"
                                onMouseDown={(e) => handleColResizeStart(e, i)}
                                title="拖拽调整列宽"
                              />
                            )}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {prs.map((pr) => {
                        const fullTitle = pr.title || ''
                        const truncated = fullTitle.length > TITLE_TRUNCATE
                        const displayTitle = truncated ? `${fullTitle.slice(0, TITLE_TRUNCATE)}…` : fullTitle
                        return (
                          <tr key={pr.number}>
                            <td className="pr-panel-cell-num">#{pr.number}</td>
                            <td
                              className="pr-panel-cell-title"
                              title={fullTitle}
                              onMouseEnter={(e) => showTitleTooltip(e, fullTitle)}
                              onMouseLeave={hideTitleTooltip}
                            >
                              {displayTitle}
                            </td>
                            <td className="pr-panel-cell-author">{pr.author || '–'}</td>
                            <td>
                              <span className={`pr-panel-state pr-panel-state-${pr.state}`}>
                                {pr.state}
                              </span>
                            </td>
                            <td className="pr-panel-cell-link">
                              <a
                                href={pr.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="pr-panel-link"
                                title="在 GitHub 中打开"
                              >
                                <ExternalLink size={14} />
                              </a>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  <p className="pr-panel-count">
                    {authorQuery ? `${authorQuery} 的 PR，共 ${prs.length} 个` : `共 ${prs.length} 个 PR`}
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        <div
          className="pr-panel-resize-handle"
          onMouseDown={handleResizeMouseDown}
          title="拖拽调整宽度"
        />
      </div>

      {tooltip.show && tooltip.text && (
        <div
          className="pr-panel-tooltip"
          style={{
            left: tooltip.x,
            top: tooltip.y - 8,
            transform: 'translate(-50%, -100%)',
          }}
          role="tooltip"
        >
          {tooltip.text}
        </div>
      )}
    </>
  )
}
