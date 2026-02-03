'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface Message {
  id: number
  text: string
  role: 'user' | 'assistant'
  isLoading?: boolean
  elapsedMs?: number
}

const MODELS = [
  { id: 'llama-8b', name: 'Llama 3 8B' },
  { id: 'mistral-7b', name: 'Mistral 7B' },
]

const SUGGESTIONS = [
  'Explain quantum computing simply',
  'Write a haiku about coding',
  'What is the meaning of life?',
]

const STORAGE_KEY = 'vmux-chat-backend'

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedModel, setSelectedModel] = useState('llama-8b')
  const [backendUrl, setBackendUrl] = useState('')
  const [showBackendModal, setShowBackendModal] = useState(false)
  const [backendInput, setBackendInput] = useState('')
  const [backendReady, setBackendReady] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const isSubmittingRef = useRef(false)

  // Load backend URL from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      setBackendUrl(saved)
      setBackendInput(saved)
    }
  }, [])

  // Check backend health
  useEffect(() => {
    if (!backendUrl) {
      setBackendReady(false)
      return
    }

    const checkHealth = async () => {
      try {
        const res = await fetch(`${backendUrl}/health`, { method: 'GET' })
        const data = await res.json()
        setBackendReady(data.ready === true)
      } catch {
        setBackendReady(false)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [backendUrl])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
  }

  const sendMessage = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim()) return
    if (isSubmittingRef.current) return
    if (!backendUrl) {
      setShowBackendModal(true)
      return
    }

    isSubmittingRef.current = true
    setIsGenerating(true)

    const userMessage: Message = {
      id: Date.now(),
      text: messageText,
      role: 'user',
    }

    const loadingMessage: Message = {
      id: Date.now() + 1,
      text: '',
      role: 'assistant',
      isLoading: true,
    }

    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInput('')
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }

    const startTime = Date.now()

    try {
      // Build conversation history
      const chatMessages = messages
        .filter(m => !m.isLoading)
        .map(m => ({ role: m.role, content: m.text }))
      chatMessages.push({ role: 'user', content: messageText })

      const res = await fetch(`${backendUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'default',
          messages: chatMessages,
          stream: true,
        }),
      })

      if (!res.ok) throw new Error('Request failed')

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const json = JSON.parse(data)
            const content = json.choices?.[0]?.delta?.content || ''
            fullText += content

            setMessages(prev => prev.map(msg =>
              msg.id === loadingMessage.id
                ? { ...msg, text: fullText }
                : msg
            ))
          } catch {}
        }
      }

      const elapsedMs = Date.now() - startTime
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id
          ? { ...msg, isLoading: false, elapsedMs }
          : msg
      ))
    } catch (e) {
      setMessages(prev => prev.map(msg =>
        msg.id === loadingMessage.id
          ? { ...msg, text: `Error: ${e instanceof Error ? e.message : 'Unknown'}`, isLoading: false }
          : msg
      ))
    }

    setIsGenerating(false)
    isSubmittingRef.current = false
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const saveBackendUrl = () => {
    if (backendInput) {
      // Normalize URL (remove trailing slash)
      const normalized = backendInput.replace(/\/$/, '')
      setBackendUrl(normalized)
      localStorage.setItem(STORAGE_KEY, normalized)
    }
    setShowBackendModal(false)
  }

  // Timer for loading messages
  const [, setTick] = useState(0)
  useEffect(() => {
    if (!isGenerating) return
    const interval = setInterval(() => setTick(t => t + 1), 100)
    return () => clearInterval(interval)
  }, [isGenerating])

  const getElapsedSeconds = (msg: Message) => {
    if (!msg.isLoading) return 0
    const loadingMsg = messages.find(m => m.id === msg.id && m.isLoading)
    if (!loadingMsg) return 0
    // Find when this message was created (its ID is timestamp)
    return Math.floor((Date.now() - msg.id) / 1000)
  }

  return (
    <main>
      {/* Backend URL Modal */}
      {showBackendModal && (
        <div className="modal-overlay" onClick={() => setShowBackendModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Connect Backend</h2>
            <p>
              Enter your vmux preview URL. Start a backend with:<br/>
              <code style={{ fontSize: 12, opacity: 0.7 }}>
                vmux run --gpu A10G -dp 8000 python backend.py
              </code>
            </p>
            <input
              type="url"
              value={backendInput}
              onChange={e => setBackendInput(e.target.value)}
              placeholder="https://your-preview-url.vmux.dev"
              onKeyDown={e => e.key === 'Enter' && saveBackendUrl()}
              autoFocus
            />
            <div className="modal-actions">
              <button className="modal-btn secondary" onClick={() => setShowBackendModal(false)}>
                Cancel
              </button>
              <button className="modal-btn primary" onClick={saveBackendUrl}>
                Connect
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="header">
        <div className="header-left">
          <span
            className={`status-dot ${!backendUrl ? 'error' : backendReady ? '' : 'loading'}`}
            onClick={() => setShowBackendModal(true)}
            style={{ cursor: 'pointer' }}
          />
          <span
            className="model-name"
            onClick={() => setShowBackendModal(true)}
            style={{ cursor: 'pointer' }}
          >
            {!backendUrl ? 'No backend' : backendReady ? 'Connected' : 'Connecting...'}
          </span>
        </div>
        <div className="header-right">
          {MODELS.map(model => (
            <button
              key={model.id}
              className={`model-btn ${selectedModel === model.id ? 'active' : ''}`}
              onClick={() => setSelectedModel(model.id)}
            >
              {model.name}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h1>vmux chat</h1>
            <p>Open-source LLMs on GPU</p>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`msg-row ${msg.role}`}>
              <div className={`bubble ${msg.role} ${msg.isLoading ? 'loading' : ''}`}>
                {msg.isLoading && !msg.text ? (
                  <div className="loading-content">
                    <div className="loading-text">
                      <span>generating...</span>
                      <span>{getElapsedSeconds(msg)}s</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${Math.min(95, getElapsedSeconds(msg) * 3)}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <>
                    {msg.text}
                    {msg.elapsedMs && !msg.isLoading && (
                      <div className="elapsed">{(msg.elapsedMs / 1000).toFixed(1)}s</div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {messages.length === 0 && (
        <div className="suggestions">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              className="suggestion-btn"
              onClick={() => sendMessage(s)}
              disabled={isGenerating || !backendReady}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="input-area">
        <div className="input-row">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={isGenerating ? 'Generating...' : 'Message'}
              className="input-field"
              rows={1}
              disabled={isGenerating}
            />
          </div>
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={!input.trim() || isGenerating}
          >
            ↑
          </button>
        </div>
      </div>
    </main>
  )
}
