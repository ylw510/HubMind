import React, { useState } from 'react'
import { Bot, User, Copy, Check, Edit2, Trash2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import 'highlight.js/styles/github-dark.css'

export default function ChatMessage({ message, role, onEdit, onDelete }) {
  const [copied, setCopied] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(message.content)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleEdit = () => {
    if (isEditing) {
      onEdit?.(editContent)
      setIsEditing(false)
    } else {
      setIsEditing(true)
    }
  }

  const handleDelete = () => {
    if (window.confirm('确定要删除这条消息吗？')) {
      onDelete?.()
    }
  }

  return (
    <div className={`chatbot-message ${role}`}>
      <div className="chatbot-message-avatar">
        {role === 'user' ? <User size={20} /> : <Bot size={20} />}
      </div>
      <div className="chatbot-message-content-wrapper">
        <div className="chatbot-message-content">
          {isEditing && role === 'user' ? (
            <textarea
              className="chatbot-message-edit-input"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onBlur={handleEdit}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleEdit()
                }
                if (e.key === 'Escape') {
                  setIsEditing(false)
                  setEditContent(message.content)
                }
              }}
              autoFocus
            />
          ) : role === 'assistant' ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, rehypeHighlight]}
              components={{
                a: ({ node, ...props }) => (
                  <a {...props} target="_blank" rel="noopener noreferrer" className="chatbot-markdown-link">
                    {props.children}
                  </a>
                ),
                h1: ({ node, ...props }) => (
                  <h1 {...props} className="chatbot-markdown-h1" />
                ),
                h2: ({ node, ...props }) => (
                  <h2 {...props} className="chatbot-markdown-h2" />
                ),
                h3: ({ node, ...props }) => (
                  <h3 {...props} className="chatbot-markdown-h3" />
                ),
                h4: ({ node, ...props }) => (
                  <h4 {...props} className="chatbot-markdown-h4" />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : (
            <p>{message.content}</p>
          )}
        </div>
        <div className="chatbot-message-actions">
          {role === 'user' && (
            <>
              <button
                type="button"
                className="chatbot-message-action"
                onClick={handleEdit}
                title="编辑"
              >
                <Edit2 size={12} />
              </button>
              <button
                type="button"
                className="chatbot-message-action"
                onClick={handleDelete}
                title="删除"
              >
                <Trash2 size={12} />
              </button>
            </>
          )}
          <button
            type="button"
            className="chatbot-message-action"
            onClick={handleCopy}
            title={copied ? '已复制' : '复制'}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
          </button>
        </div>
      </div>
    </div>
  )
}
