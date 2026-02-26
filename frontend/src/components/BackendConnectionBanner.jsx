import React, { useState, useEffect } from 'react'
import { checkBackendHealth, getApiBaseUrl, setApiBaseUrl } from '../services/api'

export function BackendConnectionBanner() {
  const [reachable, setReachable] = useState(null)
  const [apiUrlInput, setApiUrlInput] = useState(() => getApiBaseUrl())
  const [saving, setSaving] = useState(false)
  const wasZeroZero = apiUrlInput.includes('0.0.0.0')

  const check = () => {
    checkBackendHealth().then(setReachable)
  }

  useEffect(() => {
    check()
    const t = setInterval(check, 8000)
    return () => clearInterval(t)
  }, [])

  const handleSaveUrl = () => {
    setApiBaseUrl(apiUrlInput)
    setSaving(true)
    checkBackendHealth()
      .then((ok) => {
        setReachable(ok)
        setSaving(false)
      })
      .catch(() => setSaving(false))
  }

  if (reachable === true) return null

  return (
    <div className="backend-banner">
      <p className="backend-banner-text">
        {reachable === false
          ? `无法连接后端。当前地址：${getApiBaseUrl()}。请先启动后端（见下方说明）。若后端在别的电脑或远程服务器，请把地址改为 http://<那台机器的IP>:8000 并保存。`
          : '正在检测后端连接…'}
      </p>
      {reachable === false && (
        <>
          <div className="backend-banner-row">
            <input
              type="text"
              className="input backend-banner-input"
              value={apiUrlInput}
              onChange={(e) => setApiUrlInput(e.target.value)}
              placeholder="http://localhost:8000 或 http://127.0.0.1:8000"
            />
            <button
              type="button"
              className="button"
              onClick={handleSaveUrl}
              disabled={saving}
            >
              {saving ? '检测中…' : '保存并检测'}
            </button>
          </div>
          <p className="backend-banner-hint">
            启动方式（在 HubMind 项目根目录执行）：<code>python run_backend.py</code> 或 <code>cd backend && python main.py</code>
          </p>
          {wasZeroZero && (
            <p className="backend-banner-hint backend-banner-warn">
              <strong>提示：</strong> 0.0.0.0 仅用于服务端监听，浏览器无法连接。请改为 <code>http://127.0.0.1:8000</code>（本机）或 <code>http://本机IP:8000</code>（其他设备）后点击「保存并检测」。
            </p>
          )}
          <p className="backend-banner-hint">
            本机访问可填 <code>http://127.0.0.1:8000</code>；前端在本地、后端在远程时填 <code>http://远程IP:8000</code>
          </p>
        </>
      )}
    </div>
  )
}
