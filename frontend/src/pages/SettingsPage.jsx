import React, { useState, useEffect } from 'react'
import { Save, Key, Github, Lock } from 'lucide-react'
import api from '../services/api'

const LLM_PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic Claude' },
  { value: 'google', label: 'Google Gemini' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'groq', label: 'Groq' },
  { value: 'ollama', label: 'Ollama (本地)' },
  { value: 'openai_compatible', label: '自定义 (OpenAI 兼容 API)' },
]

function SettingsPage() {
  const [githubToken, setGithubToken] = useState('')
  const [llmProvider, setLlmProvider] = useState('deepseek')
  const [llmApiKey, setLlmApiKey] = useState('')
  const [llmBaseUrl, setLlmBaseUrl] = useState('')
  const [llmModel, setLlmModel] = useState('')
  const [hasGithubToken, setHasGithubToken] = useState(false)
  const [hasLlmKey, setHasLlmKey] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  // 修改密码
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [passwordMessage, setPasswordMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    api.get('/api/settings')
      .then((res) => {
        setLlmProvider(res.data.llm_provider || 'deepseek')
        setLlmBaseUrl(res.data.llm_base_url || '')
        setLlmModel(res.data.llm_model || '')
        setHasGithubToken(!!(res.data.github_token && res.data.github_token.startsWith('***')))
        setHasLlmKey(!!(res.data.llm_api_key && res.data.llm_api_key.startsWith('***')))
      })
      .catch(() => setMessage({ type: 'error', text: '获取设置失败' }))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    setSaving(true)
    try {
      await api.put('/api/settings', {
        ...(githubToken ? { github_token: githubToken } : {}),
        llm_provider: llmProvider,
        ...(llmApiKey ? { llm_api_key: llmApiKey } : {}),
        ...(llmProvider === 'openai_compatible' ? { llm_base_url: llmBaseUrl.trim(), llm_model: llmModel.trim() } : {}),
      })
      setMessage({ type: 'success', text: '设置已保存' })
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setPasswordMessage({ type: '', text: '' })
    if (newPassword.length < 6) {
      setPasswordMessage({ type: 'error', text: '新密码至少 6 位' })
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: '两次输入的新密码不一致' })
      return
    }
    setPasswordSaving(true)
    try {
      await api.put('/api/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setPasswordMessage({ type: 'success', text: '密码已修改' })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setPasswordMessage({ type: 'error', text: err.response?.data?.detail || '修改失败' })
    } finally {
      setPasswordSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading">加载中...</div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <h1 className="page-title">⚙️ 设置</h1>
      <p className="page-description">配置 GitHub Token 与 LLM 密钥，登录后 API 将使用你的配置</p>

      <form onSubmit={handleSubmit} className="card settings-form">
        <div className="settings-section">
          <h3 className="board-title">
            <Github size={18} />
            GitHub Token
          </h3>
          <input
            type="password"
            className="input"
            placeholder={hasGithubToken ? '已设置，输入新 Token 以覆盖' : 'ghp_xxxxxxxxxxxx'}
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            autoComplete="off"
          />
          <p className="settings-hint">用于访问 GitHub API，需 repo 等权限</p>
        </div>

        <div className="settings-section">
          <h3 className="board-title">
            <Key size={18} />
            LLM 提供商
          </h3>
          <select
            className="input"
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value)}
          >
            {LLM_PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          {llmProvider === 'openai_compatible' && (
            <>
              <input
                type="url"
                className="input"
                placeholder="API 地址 (base_url)，如 https://api.example.com/v1"
                value={llmBaseUrl}
                onChange={(e) => setLlmBaseUrl(e.target.value)}
                autoComplete="off"
                style={{ marginTop: '8px' }}
              />
              <input
                type="text"
                className="input"
                placeholder="模型名称 (model_name)，必填"
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                autoComplete="off"
                style={{ marginTop: '6px' }}
              />
              <p className="settings-hint">任意兼容 OpenAI 格式的 API，填写 base_url 与模型名</p>
            </>
          )}
        </div>

        <div className="settings-section">
          <h3 className="board-title">LLM API Key</h3>
          <input
            type="password"
            className="input"
            placeholder={hasLlmKey ? '已设置，输入新 Key 以覆盖' : 'API Key（Ollama 可留空）'}
            value={llmApiKey}
            onChange={(e) => setLlmApiKey(e.target.value)}
            autoComplete="off"
          />
        </div>

        {message.text && (
          <div className={message.type === 'success' ? 'success' : 'error'}>
            {message.text}
          </div>
        )}

        <button type="submit" className="button" disabled={saving}>
          <Save size={18} />
          {saving ? '保存中...' : '保存设置'}
        </button>
      </form>

      <form onSubmit={handleChangePassword} className="card settings-form settings-password-form">
        <div className="settings-section">
          <h3 className="board-title">
            <Lock size={18} />
            修改密码
          </h3>
          <input
            type="password"
            className="input"
            placeholder="当前密码"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <input
            type="password"
            className="input"
            placeholder="新密码（至少 6 位）"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          <input
            type="password"
            className="input"
            placeholder="确认新密码"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          {passwordMessage.text && (
            <div className={passwordMessage.type === 'success' ? 'success' : 'error'}>
              {passwordMessage.text}
            </div>
          )}
          <button type="submit" className="button" disabled={passwordSaving}>
            <Lock size={18} />
            {passwordSaving ? '修改中...' : '修改密码'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default SettingsPage
