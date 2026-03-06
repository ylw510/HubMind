import React, { useState, useRef, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Send, Bot, Plus, Image as ImageIcon, X } from 'lucide-react'
import { chatAPI, issueAPI } from '../services/api'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import RepoSelector from '../components/RepoSelector'
import IssuePanel from '../components/IssuePanel'
import PRPanel from '../components/PRPanel'
import '../styles/chatbot.css'

function ChatPage() {
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [selectedRepo, setSelectedRepo] = useState('')
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [showIssuePanel, setShowIssuePanel] = useState(false)
  const [issueDraft, setIssueDraft] = useState({ text: '', repo: '' })
  const [showPRPanel, setShowPRPanel] = useState(false)
  const [prPanelQuery, setPrPanelQuery] = useState('')
  const [attachedImages, setAttachedImages] = useState([])
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const queryClient = useQueryClient()
  const isInitialLoadRef = useRef(true) // 标记是否是初始加载
  const isStreamingRef = useRef(false) // 使用 ref 跟踪流式状态，避免依赖项问题

  // 获取所有对话会话
  const {
    data: sessionsData,
    isLoading: sessionsLoading,
  } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: () => chatAPI.getSessions(),
    staleTime: 1000 * 30, // 30秒内不重新获取
  })

  const chatSessions = sessionsData?.sessions || []

  // 获取当前会话的详细信息（包括消息历史）
  const {
    data: currentSessionData,
    isLoading: sessionLoading,
  } = useQuery({
    queryKey: ['chat-session', currentSessionId],
    queryFn: () => chatAPI.getSession(currentSessionId),
    enabled: !!currentSessionId && currentSessionId !== 'current',
    staleTime: 0, // 总是获取最新数据
  })

  // 当会话数据加载完成时，恢复历史记录
  useEffect(() => {
    // 如果正在流式输出，不要覆盖历史记录
    if (isStreamingRef.current) {
      return
    }

    if (currentSessionData && currentSessionId) {
      // 从数据库加载的消息，确保完全替换当前历史
      const loadedMessages = currentSessionData.messages || []

      // 初始加载时，直接设置历史记录
      if (isInitialLoadRef.current) {
        setChatHistory(loadedMessages)
        setSelectedRepo(currentSessionData.repo || '')
        isInitialLoadRef.current = false
        return
      }

      // 非初始加载时，只有当加载的消息与当前历史不同时才更新
      // 并且只有当本地历史为空或者加载的消息数量更多时才更新（避免用旧数据覆盖新数据）
      const currentHistoryLength = chatHistory.length
      const loadedMessagesLength = loadedMessages.length

      // 只有在以下情况才更新：
      // 1. 本地历史为空（可能是切换会话）
      // 2. 加载的消息数量明显多于本地历史（说明数据库有更新）
      // 3. 消息内容确实不同且加载的消息数量不少于本地历史（避免用旧数据覆盖）
      if (currentHistoryLength === 0 ||
          (loadedMessagesLength > currentHistoryLength && loadedMessagesLength - currentHistoryLength > 1) ||
          (JSON.stringify(loadedMessages) !== JSON.stringify(chatHistory) && loadedMessagesLength >= currentHistoryLength)) {
        setChatHistory(loadedMessages)
      }
      setSelectedRepo(currentSessionData.repo || '')
    } else if (currentSessionId === null) {
      // 新对话，清空历史
      setChatHistory([])
      setSelectedRepo('')
      isInitialLoadRef.current = true
    }
  }, [currentSessionData, currentSessionId])

  // 检测消息中是否包含创建 issue 的意图
  const detectIssueIntent = (text) => {
    const issueKeywords = [
      'create issue', '创建 issue', '提 issue', '新建 issue',
      'open issue', '提交 issue', 'report issue', '报告问题',
      'create a bug', '创建 bug', '提 bug', '报告 bug',
      'new issue', '我要提', '我想提', '帮我提'
    ]
    const lowerText = text.toLowerCase()
    // 检查是否包含明确的创建意图
    const hasExplicitIntent = issueKeywords.some(keyword => lowerText.includes(keyword))
    // 或者包含 "issue" 或 "问题" 且长度足够（可能是描述性的）
    const hasIssueKeyword = (lowerText.includes('issue') || lowerText.includes('问题') || lowerText.includes('bug')) && text.length > 10
    return hasExplicitIntent || (hasIssueKeyword && showIssuePanel === false)
  }

  // 检测「查看 XXX 项目今天的 PR」意图
  const detectPRListIntent = (text) => {
    const lower = text.toLowerCase().trim()
    const hasPR = /\bpr\b|pull\s*request|合并请求|今日.*pr|今天.*pr|今天的\s*pr/i.test(lower)
    const hasToday = /今天|今日|today/i.test(lower)
    const hasView = /查看|看看|帮我查|想看/i.test(lower)
    const hasProject = /项目|repo|仓库|repository/i.test(lower) || /[\w\u4e00-\u9fa5\-]{2,}/.test(text)
    return hasPR && (hasToday || hasView) && hasProject
  }

  // 从消息中提取项目名（用于搜索仓库）：只取英文/数字/斜杠，避免把「今天的pr」等中文带进去
  const extractProjectNameForPR = (text) => {
    // 优先：查看/看看 + 纯英文数字的仓库名（如 ClickHouse、Vue、facebook/react）
    const m = text.match(/(?:帮我)?(?:查看|看看|查一下)\s*([a-zA-Z0-9_\-/]+)/i)
    if (m) return m[1].trim()
    // 备选：在「今天/今日」之前的英文数字段
    const m2 = text.match(/([a-zA-Z0-9_\-/]{2,})\s*(?:项目|仓库)?\s*(?:今天|今日)/i)
    if (m2) return m2[1].trim()
    // 兜底：整句里第一段连续英文/数字
    const m3 = text.match(/([a-zA-Z0-9_\-/]{2,})/)
    return m3 ? m3[1].trim() : text.replace(/\s+/g, ' ').trim().slice(0, 30)
  }

  // 从消息中提取 issue 描述
  const extractIssueText = (text) => {
    // 移除常见的触发词，但保留完整内容
    const cleaned = text
      .replace(/^(create|创建|提|新建|open|提交|report|报告|我要提|我想提|帮我提|帮我创建)\s*(an?\s*)?(issue|bug|问题)[,，:：]?\s*/i, '')
      .trim()
    // 如果清理后为空，使用原始文本
    return cleaned || text
  }

  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory, streamingMessage])

  const mutation = useMutation({
    mutationFn: ({ message: msg, history }) => {
      // 使用流式模式
      setIsStreaming(true)
      isStreamingRef.current = true
      setStreamingMessage('')

      return chatAPI.chat(
        msg,
        history, // 使用传入的最新历史记录（包含用户消息）
        selectedRepo || null,
        currentSessionId,
        (chunk, done) => {
          // 实时更新流式消息
          setStreamingMessage((prev) => {
            const newContent = prev + chunk
            return newContent
          })
          if (done) {
            setIsStreaming(false)
            isStreamingRef.current = false
          }
        }
      )
    },
    onSuccess: async (data) => {
      setIsStreaming(false)
      isStreamingRef.current = false

      // 清空已附加的图片
      attachedImages.forEach(img => {
        URL.revokeObjectURL(img.preview)
      })
      setAttachedImages([])

      // 将流式消息添加到历史记录（用户消息已经在发送时添加了）
      const assistantMessage = streamingMessage || data.response

      // 使用函数式更新确保使用最新的历史记录
      let updatedHistory = []
      setChatHistory(prev => {
        // 确保最后一条消息是用户消息，然后添加 AI 回复
        updatedHistory = [...prev, { role: 'assistant', content: assistantMessage }]
        return updatedHistory
      })

      setStreamingMessage('')

      // 从更新后的历史记录中获取用户消息（最后一条用户消息）
      const userMessages = updatedHistory.filter(m => m.role === 'user')
      const lastUserMessage = userMessages.length > 0 ? userMessages[userMessages.length - 1].content : ''

      // 如果是新对话，创建会话并保存历史
      if (!currentSessionId || currentSessionId === 'current') {
        const newSessionId = await createNewSession(lastUserMessage, updatedHistory)
        // 创建会话后，历史已经保存，直接设置
        if (newSessionId) {
          // 等待一下，确保数据已保存，然后刷新
          setTimeout(() => {
            queryClient.invalidateQueries(['chat-session', newSessionId])
          }, 200)
        }
      } else {
        // 已有会话，刷新当前会话数据，确保从数据库加载最新数据
        queryClient.invalidateQueries(['chat-session', currentSessionId])
      }

      // 如果 issue 面板已打开，尝试更新 issue 内容
      if (showIssuePanel && issueDraft.repo) {
        updateIssueFromMessage(lastUserMessage, updatedHistory)
      }

      // 更新会话标题（只在新会话创建后更新）
      if (updatedHistory.length > 0) {
        const firstUserMessage = updatedHistory.find(m => m.role === 'user')
        if (firstUserMessage) {
          // 如果刚创建了新会话，标题会在 createNewSession 中设置
          // 如果是已有会话，更新标题
          if (currentSessionId && currentSessionId !== 'current') {
            updateSessionTitle(currentSessionId, firstUserMessage.content.slice(0, 30))
          }
        }
      }
    },
  })

  // 创建新会话
  const createNewSession = async (firstMessage, history) => {
    try {
      const title = firstMessage.slice(0, 30) || 'New chat'
      const newSession = await chatAPI.createSession(title, selectedRepo || null)
      const newSessionId = newSession.id
      setCurrentSessionId(newSessionId)

      // 保存历史消息到新会话（如果存在）
      if (history && history.length > 0) {
        try {
          // 将历史消息保存到数据库
          await saveHistoryToSession(newSessionId, history)
        } catch (e) {
          console.error('Failed to save history to new session:', e)
        }
      }

      // 刷新会话列表
      queryClient.invalidateQueries(['chat-sessions'])

      // 返回新会话 ID，供调用者使用
      return newSessionId
    } catch (e) {
      console.error('Failed to create session:', e)
      return null
    }
  }

  // 保存历史消息到会话
  const saveHistoryToSession = async (sessionId, history) => {
    try {
      if (history && history.length > 0) {
        await chatAPI.saveMessages(sessionId, history)
        // 刷新当前会话数据
        queryClient.invalidateQueries(['chat-session', sessionId])
      }
    } catch (e) {
      console.error('Failed to save history:', e)
    }
  }

  // 更新会话标题
  const updateSessionTitle = async (sessionId, title) => {
    if (!sessionId || sessionId === 'current') return
    try {
      await chatAPI.updateSession(sessionId, title)
      queryClient.invalidateQueries(['chat-sessions'])
    } catch (e) {
      console.error('Failed to update session title:', e)
    }
  }

  // 处理 issue 创建意图 - 在发送给 agent 之前拦截
  const handleIssueIntent = (userMessage) => {
    // 提取 issue 文本（保留完整内容，不只是移除触发词）
    let issueText = extractIssueText(userMessage)
    // 如果提取后为空，使用原始消息
    if (!issueText || issueText.trim() === '') {
      issueText = userMessage
    }

    // 优先使用已选择的仓库，否则尝试从历史消息中提取
    const issueRepo = selectedRepo || extractRepoFromMessage(chatHistory)

    if (selectedRepo || issueRepo) {
      // 添加用户消息到历史
      const newUserMsg = { role: 'user', content: userMessage }
      const newAssistantMsg = {
        role: 'assistant',
        content: '✅ 我已经为你准备好了 Issue 内容，请在右侧面板中查看和编辑。确认无误后点击"Submit new issue"按钮提交。'
      }
      setChatHistory(prev => [...prev, newUserMsg, newAssistantMsg])

      // 打开 issue 面板并填充内容
      // 注意：先设置 showIssuePanel，再设置 issueDraft，确保组件能正确接收 initialText
      setShowIssuePanel(true)
      setIssueDraft({
        text: issueText,
        repo: selectedRepo || issueRepo
      })
      return true // 表示已处理，不需要发送给 agent
    } else {
      // 如果没有指定仓库，提示用户选择
      const newUserMsg = { role: 'user', content: userMessage }
      const newAssistantMsg = {
        role: 'assistant',
        content: '⚠️ 请先在上方选择仓库，然后我可以帮你创建 Issue。'
      }
      setChatHistory(prev => [...prev, newUserMsg, newAssistantMsg])
      return true // 已处理，不需要发送给 agent
    }
  }

  // 处理「查看项目今日 PR」意图：展示用户消息并打开 PR 面板（带确认工作流）
  const handlePRListIntent = (userMessage) => {
    const projectName = extractProjectNameForPR(userMessage)
    if (!projectName) return false
    setChatHistory(prev => [...prev,
      { role: 'user', content: userMessage },
      { role: 'assistant', content: '✅ 正在查找您说的项目，请在右侧面板确认是否为要查看的仓库，确认后将加载今日 PR 列表。' }
    ])
    setPrPanelQuery(projectName)
    setShowPRPanel(true)
    return true
  }

  // 从消息历史中提取仓库名
  const extractRepoFromMessage = (history) => {
    for (const msg of history.reverse()) {
      if (msg.role === 'user' && /[\w\-\.]+\/[\w\-\.]+/.test(msg.content)) {
        const match = msg.content.match(/([\w\-\.]+\/[\w\-\.]+)/)
        if (match) return match[1]
      }
    }
    return ''
  }

  // 根据对话更新 issue 内容
  const updateIssueFromMessage = async (userMessage, history) => {
    if (!issueDraft.repo || !showIssuePanel) return

    // 检测用户是否在修改 issue
    const updateKeywords = ['修改', '改成', '改为', '更新', 'change', 'update', 'modify', 'edit', '标题', '内容', '描述', '添加', 'add', '补充']
    const lowerMsg = userMessage.toLowerCase()

    // 如果包含更新关键词，或者用户明确提到要修改 issue
    if (updateKeywords.some(kw => lowerMsg.includes(kw)) || lowerMsg.includes('issue') || lowerMsg.includes('问题')) {
      try {
        // 结合原始文本和新的修改指令
        const combinedText = `${issueDraft.text}\n\n用户修改要求: ${userMessage}`

        // 更新 issue draft，触发 IssuePanel 重新解析
        setIssueDraft(prev => ({
          ...prev,
          text: combinedText,
        }))
      } catch (e) {
        console.error('Failed to update issue:', e)
      }
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!message.trim() || mutation.isPending) return

    const userMessage = message.trim()

    // 如果检测到 issue 创建意图，先处理 issue 面板，不发送给 agent
    if (detectIssueIntent(userMessage) && !showIssuePanel) {
      if (handleIssueIntent(userMessage)) {
        setMessage('')
        return
      }
    }

    // 如果检测到「查看 XXX 项目今天的 PR」意图，打开 PR 面板（带确认工作流），不发送给 agent
    if (detectPRListIntent(userMessage) && !showPRPanel) {
      if (handlePRListIntent(userMessage)) {
        setMessage('')
        return
      }
    }

    // 如果有图片，在消息前添加图片描述
    let finalUserMessage = userMessage
    if (attachedImages.length > 0) {
      const imageInfo = attachedImages.map((img, idx) =>
        `[图片 ${idx + 1}: ${img.name}]`
      ).join('\n')
      finalUserMessage = `${imageInfo}\n\n${userMessage}`
    }

    // 立即将用户消息添加到历史记录，这样用户消息会立即显示
    const userMsg = { role: 'user', content: finalUserMessage }
    setChatHistory(prev => [...prev, userMsg])
    setMessage('') // 立即清空输入框

    // 立即设置流式状态，显示加载指示器
    setIsStreaming(true)
    setStreamingMessage('')

    // 构建包含用户消息的最新历史记录
    const updatedHistoryWithUser = [...chatHistory, userMsg]

    // 如果 issue 面板已打开，尝试更新 issue 内容
    if (showIssuePanel && issueDraft.repo) {
      // 继续对话，但也会更新 issue
      mutation.mutate({ message: finalUserMessage, history: updatedHistoryWithUser })
      return
    }

    // 正常发送给 agent
    mutation.mutate({ message: finalUserMessage, history: updatedHistoryWithUser })
  }

  const handleNewChat = () => {
    setChatHistory([])
    setSelectedRepo('')
    setCurrentSessionId(null)
    setShowIssuePanel(false)
    setIssueDraft({ text: '', repo: '' })
    setShowPRPanel(false)
    setPrPanelQuery('')
    setMessage('')
  }

  const handleSelectSession = (sessionId) => {
    setCurrentSessionId(sessionId)
    isInitialLoadRef.current = true // 切换会话时标记为初始加载
    // 历史记录会通过 useQuery 自动加载
  }

  const handleDeleteSession = async (sessionId) => {
    if (sessionId === currentSessionId) {
      // 如果删除的是当前会话，切换到新对话
      handleNewChat()
    }
    try {
      await chatAPI.deleteSession(sessionId)
      queryClient.invalidateQueries(['chat-sessions'])
    } catch (e) {
      console.error('Failed to delete session:', e)
    }
  }

  const handleEditMessage = (index, newContent) => {
    const updatedHistory = [...chatHistory]
    updatedHistory[index] = { ...updatedHistory[index], content: newContent }
    setChatHistory(updatedHistory)
  }

  const handleDeleteMessage = (index) => {
    const updatedHistory = chatHistory.filter((_, i) => i !== index)
    setChatHistory(updatedHistory)
  }

  const handleSelectRepo = (repoFullName) => {
    setSelectedRepo(repoFullName)
  }

  const handleRemoveRepo = () => {
    setSelectedRepo('')
  }

  // 处理图片选择
  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    const newImages = files.map(file => {
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        alert('请选择图片文件')
        return null
      }

      // 验证文件大小（限制为 5MB）
      if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过 5MB')
        return null
      }

      return {
        file,
        preview: URL.createObjectURL(file),
        name: file.name
      }
    }).filter(Boolean)

    setAttachedImages(prev => [...prev, ...newImages])

    // 清空 input，允许重复选择同一文件
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 移除图片
  const handleRemoveImage = (index) => {
    setAttachedImages(prev => {
      const newImages = [...prev]
      // 释放预览 URL
      URL.revokeObjectURL(newImages[index].preview)
      newImages.splice(index, 1)
      return newImages
    })
  }

  // 清理所有图片预览 URL
  useEffect(() => {
    return () => {
      attachedImages.forEach(img => {
        URL.revokeObjectURL(img.preview)
      })
    }
  }, [attachedImages])

  const handleIssueCreated = (issueData) => {
    // Issue 创建成功后的处理
    const successMessage = `✅ Issue 创建成功！\n\n**#${issueData.number}**: ${issueData.title}\n**URL**: ${issueData.url}`
    setChatHistory(prev => [...prev, {
      role: 'assistant',
      content: successMessage
    }])
  }

  const handleCloseIssuePanel = () => {
    setShowIssuePanel(false)
    setIssueDraft({ text: '', repo: '' })
  }

  const handleClosePRPanel = () => {
    setShowPRPanel(false)
    setPrPanelQuery('')
  }

  return (
    <div className={`chatbot-layout ${showIssuePanel ? 'with-issue-panel' : ''} ${showPRPanel ? 'with-pr-panel' : ''}`}>
      <Sidebar
        sessions={chatSessions}
        currentSessionId={currentSessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <main className="chatbot-main">
        <div className="chatbot-content">
          <div className={`chatbot-messages ${showIssuePanel ? 'with-panel' : ''} ${showPRPanel ? 'with-pr-panel' : ''}`}>
            {chatHistory.length === 0 && (
              <div className="chatbot-empty">
                <div className="chatbot-empty-icon">
                  <Bot size={64} />
                </div>
                <h2 className="chatbot-empty-title">HubMind</h2>
                <p className="chatbot-empty-subtitle">
                  {selectedRepo
                    ? `正在查看仓库: ${selectedRepo}`
                    : '开始与 HubMind 对话，探索 GitHub 世界'}
                </p>
              </div>
            )}

            {chatHistory.map((msg, idx) => (
              <ChatMessage
                key={idx}
                message={msg}
                role={msg.role}
                onEdit={(newContent) => handleEditMessage(idx, newContent)}
                onDelete={() => handleDeleteMessage(idx)}
              />
            ))}

            {/* 显示流式消息（如果有内容） */}
            {isStreaming && streamingMessage && (
              <ChatMessage
                message={{ content: streamingMessage }}
                role="assistant"
              />
            )}

            {/* 显示加载指示器：当正在流式响应但还没有内容时，或者 mutation 正在 pending 时 */}
            {(isStreaming && !streamingMessage) || (mutation.isPending && !isStreaming) ? (
              <div className="chatbot-message assistant">
                <div className="chatbot-message-avatar">
                  <Bot size={20} />
                </div>
                <div className="chatbot-message-content-wrapper">
                  <div className="chatbot-message-content">
                    <div className="chatbot-typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-input-area">
            <form onSubmit={handleSubmit} className="chatbot-input-form">
              <div className="chatbot-input-container">
                {/* 图片预览区域 */}
                {attachedImages.length > 0 && (
                  <div className="chatbot-attached-images">
                    {attachedImages.map((img, idx) => (
                      <div key={idx} className="chatbot-attached-image-item">
                        <img src={img.preview} alt={`附件 ${idx + 1}`} />
                        <button
                          type="button"
                          className="chatbot-attached-image-remove"
                          onClick={() => handleRemoveImage(idx)}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="chatbot-input-wrapper">
                  {/* 加号按钮 - 添加图片 */}
                  <button
                    type="button"
                    className="chatbot-add-attachment-btn"
                    onClick={() => fileInputRef.current?.click()}
                    title="添加图片"
                  >
                    <Plus size={20} />
                  </button>

                  {/* 隐藏的文件输入 */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    style={{ display: 'none' }}
                    onChange={handleImageSelect}
                  />

                  <textarea
                    className="chatbot-input"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="有疑问，尽管问"
                    disabled={mutation.isPending}
                    rows={1}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSubmit(e)
                      }
                    }}
                  />
                </div>
                <div className="chatbot-input-actions">
                  <div className="chatbot-input-action-left">
                    <button
                      type="button"
                      className="chatbot-ask-btn"
                      onClick={handleSubmit}
                      disabled={!message.trim() || mutation.isPending}
                    >
                      <Send size={16} />
                      <span>Ask</span>
                    </button>
                    <div className="chatbot-repo-selector-inline">
                      <RepoSelector
                        selectedRepo={selectedRepo}
                        onSelectRepo={handleSelectRepo}
                        onRemoveRepo={handleRemoveRepo}
                      />
                    </div>
                  </div>
                  <div className="chatbot-input-action-right">
                    <button
                      type="submit"
                      className="chatbot-send-btn"
                      disabled={!message.trim() || mutation.isPending}
                      title="发送 (Enter)"
                    >
                      <Send size={18} />
                    </button>
                  </div>
                </div>
              </div>
            </form>
            <div className="chatbot-footer">
              <span className="chatbot-footer-text">
                HubMind uses AI. Check for mistakes.
              </span>
            </div>
          </div>
        </div>
      </main>

      {showIssuePanel && issueDraft.repo && issueDraft.text && (
        <IssuePanel
          key={`${issueDraft.repo}-${issueDraft.text.slice(0, 50)}-${Date.now()}`}
          repo={issueDraft.repo}
          initialText={issueDraft.text}
          onClose={handleCloseIssuePanel}
          onIssueCreated={handleIssueCreated}
        />
      )}

      {showPRPanel && prPanelQuery && (
        <PRPanel
          initialQuery={prPanelQuery}
          onClose={handleClosePRPanel}
        />
      )}
    </div>
  )
}

export default ChatPage
