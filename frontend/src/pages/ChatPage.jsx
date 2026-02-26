import React, { useState, useRef, useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Send, Bot, User, TrendingUp, GitPullRequest, Heart, HelpCircle, Zap, MessageSquare, LayoutGrid, RefreshCw, ExternalLink, Star } from 'lucide-react'
import { chatAPI, trendingAPI } from '../services/api'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'

const TRENDING_PAGE_SIZE = 5
const TRENDING_LIMIT = 20

const SUGGESTED_PROMPTS = [
  '给我看看今天最火的 5 个项目',
  '分析 microsoft/vscode 最近的 PR',
  'facebook/react 仓库健康度如何？',
  '如何在 GitHub 上创建一个新 Issue？',
]

const QUICK_LINKS = [
  { path: '/trending', icon: TrendingUp, label: '热门项目' },
  { path: '/prs', icon: GitPullRequest, label: 'PR 分析' },
  { path: '/health', icon: Heart, label: '仓库健康度' },
  { path: '/qa', icon: HelpCircle, label: '智能问答' },
]

function ChatPage() {
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [trendingPage, setTrendingPage] = useState(0)
  const messagesEndRef = useRef(null)
  const trendingScrollRef = useRef(null)

  const {
    data: trendingData,
    isLoading: trendingLoading,
    isFetching: trendingFetching,
    refetch: refetchTrending,
  } = useQuery({
    queryKey: ['trending-sidebar', 'daily'],
    queryFn: () => trendingAPI.getTrending(null, 'daily', TRENDING_LIMIT),
    staleTime: 1000 * 60 * 5,
    refetchOnWindowFocus: false,
  })

  const trendingRepos = trendingData?.repos ?? []
  const trendingPages = Math.max(1, Math.ceil(trendingRepos.length / TRENDING_PAGE_SIZE))

  useEffect(() => {
    const target = document.getElementById(`trending-page-${trendingPage}`)
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [trendingPage])

  useEffect(() => {
    const el = trendingScrollRef.current
    if (!el || trendingRepos.length === 0) return
    const onScroll = () => {
      const pages = el.querySelectorAll('.board-trending-page')
      if (pages.length === 0) return
      const scrollTop = el.scrollTop
      const containerHeight = el.clientHeight
      let page = 0
      for (let i = 0; i < pages.length; i++) {
        const top = (pages[i]?.offsetTop ?? 0) - containerHeight / 3
        if (scrollTop >= top) page = i
      }
      setTrendingPage((p) => (p !== page ? page : p))
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [trendingRepos.length])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])

  const mutation = useMutation({
    mutationFn: (msg) => chatAPI.chat(msg, chatHistory),
    onSuccess: (data) => {
      setChatHistory(data.chat_history)
      setMessage('')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!message.trim() || mutation.isPending) return
    mutation.mutate(message)
  }

  const handleSuggestedClick = (text) => {
    setMessage(text)
  }

  const userTurns = chatHistory.filter((m) => m.role === 'user').map((m) => m.content)
  const lastUserMessages = userTurns.slice(-3).reverse()

  return (
    <div className="chat-page-with-boards">
      <section className="chat-boards-top" aria-label="看板">
        <div className="board board-suggested">
          <h3 className="board-title">
            <Zap size={18} />
            推荐问题
          </h3>
          <ul className="board-list">
            {SUGGESTED_PROMPTS.map((prompt, i) => (
              <li key={i}>
                <button
                  type="button"
                  className="board-item"
                  onClick={() => handleSuggestedClick(prompt)}
                >
                  <MessageSquare size={14} className="board-item-icon" />
                  <span>{prompt}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="board board-quick">
          <h3 className="board-title">
            <LayoutGrid size={18} />
            快捷入口
          </h3>
          <ul className="board-list">
            {QUICK_LINKS.map((item) => {
              const Icon = item.icon
              return (
                <li key={item.path}>
                  <Link to={item.path} className="board-item board-link">
                    <Icon size={14} className="board-item-icon" />
                    <span>{item.label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>

        <div className="board board-trending">
          <div className="board-trending-head">
            <h3 className="board-title">
              <TrendingUp size={18} />
              Trending 实时
            </h3>
            <button
              type="button"
              className="board-trending-refresh"
              onClick={() => refetchTrending()}
              disabled={trendingFetching}
              title="重新获取"
              aria-label="刷新热门"
            >
              <RefreshCw size={16} className={trendingFetching ? 'spin' : ''} />
              <span>{trendingFetching ? '获取中…' : '刷新'}</span>
            </button>
          </div>
          <div className="board-trending-scroll" ref={trendingScrollRef}>
            {trendingLoading ? (
              <div className="board-trending-loading">加载热门中…</div>
            ) : trendingRepos.length === 0 ? (
              <div className="board-trending-empty">暂无数据，点击刷新</div>
            ) : (
              <div className="board-trending-pages">
                {Array.from({ length: trendingPages }, (_, p) => (
                  <div key={p} id={`trending-page-${p}`} className="board-trending-page">
                    {trendingRepos
                      .slice(p * TRENDING_PAGE_SIZE, (p + 1) * TRENDING_PAGE_SIZE)
                      .map((repo, i) => (
                        <a
                          key={repo.name}
                          href={repo.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="board-trending-card"
                          style={{ animationDelay: `${i * 0.04}s` }}
                        >
                          <span className="board-trending-name">{repo.name}</span>
                          {(repo.description || '').trim() && (
                            <span className="board-trending-desc">
                              {(repo.description || '').trim().slice(0, 56)}
                              {(repo.description || '').trim().length > 56 ? '…' : ''}
                            </span>
                          )}
                          <div className="board-trending-meta">
                            <span className="board-trending-stars">
                              <Star size={12} />
                              {repo.stars >= 1000 ? `${(repo.stars / 1000).toFixed(1)}k` : repo.stars}
                            </span>
                            {repo.language && (
                              <span className="board-trending-lang">{repo.language}</span>
                            )}
                          </div>
                          <ExternalLink size={12} className="board-trending-external" />
                        </a>
                      ))}
                  </div>
                ))}
              </div>
            )}
          </div>
          {trendingRepos.length > 0 && trendingPages > 1 && (
            <div className="board-trending-dots">
              {Array.from({ length: trendingPages }, (_, i) => (
                <button
                  key={i}
                  type="button"
                  className={`board-trending-dot ${i === trendingPage ? 'active' : ''}`}
                  onClick={() => setTrendingPage(i)}
                  aria-label={`第 ${i + 1} 页`}
                />
              ))}
            </div>
          )}
        </div>

        {chatHistory.length > 0 && (
          <div className="board board-summary">
            <h3 className="board-title">
              <MessageSquare size={18} />
              会话摘要
            </h3>
            <div className="board-summary-count">
              <span className="board-summary-num">{chatHistory.length}</span>
              <span> 条消息</span>
            </div>
            {lastUserMessages.length > 0 && (
              <ul className="board-list board-recent">
                {lastUserMessages.map((content, i) => (
                  <li key={i}>
                    <button
                      type="button"
                      className="board-item board-item-small"
                      onClick={() => handleSuggestedClick(content)}
                    >
                      {content.length > 28 ? `${content.slice(0, 28)}…` : content}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      <div className="chat-main">
        <h1 className="page-title">💬 智能对话</h1>
        <p className="page-description">与 HubMind 对话，探索 GitHub 世界</p>

        <div className="card chat-layout">
          <div className="chat-messages">
            {chatHistory.length === 0 && (
              <div className="chat-empty">
                <Bot size={48} className="chat-empty-icon" />
                <p>开始与 HubMind 对话吧！</p>
                <p className="chat-empty-hint">
                  试试：「给我看看今天最火的5个项目」
                </p>
              </div>
            )}
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`chat-row ${msg.role}`}>
                <div className={`chat-avatar ${msg.role}`}>
                  {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div className={`chat-bubble ${msg.role}`}>
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    <p style={{ margin: 0 }}>{msg.content}</p>
                  )}
                </div>
              </div>
            ))}
            {mutation.isPending && (
              <div className="chat-row assistant">
                <div className="chat-avatar assistant">
                  <Bot size={20} />
                </div>
                <div className="chat-bubble assistant">思考中...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="chat-form">
            <input
              type="text"
              className="input"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="输入你的问题..."
              disabled={mutation.isPending}
            />
            <button
              type="submit"
              className="button"
              disabled={!message.trim() || mutation.isPending}
            >
              <Send size={18} />
            </button>
          </form>
        </div>

        {mutation.isError && (
          <div className="error">
            错误: {mutation.error?.response?.data?.detail || mutation.error?.message}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatPage
