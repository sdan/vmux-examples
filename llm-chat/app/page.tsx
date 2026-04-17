'use client'

import { useState, useEffect, useRef, useCallback, memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: number
  text: string
  role: 'user' | 'assistant'
  isStreaming?: boolean
  elapsedMs?: number
  tokenCount?: number
}

interface HealthStatus {
  ready: boolean
  model: string
  stage?: string
}

const SUGGESTIONS = [
  'Explain how transformers work',
  'Write a Python quicksort',
  'What makes a good API?',
]

const API_BASE = ''

// Memoized message bubble
const MessageBubble = memo(function MessageBubble({
  msg,
  elapsedSeconds,
  onCopy
}: {
  msg: Message
  elapsedSeconds?: number
  onCopy: (text: string) => void
}) {
  const isLoading = msg.isStreaming && !msg.text

  return (
    <div className={msg.role === 'user' ? 'row-right' : 'row-left'}>
      <div className={`bubble ${msg.role}${isLoading ? ' loading' : ''}`}>
        {isLoading ? (
          <div className="loading-content">
            <div className="loading-text">
              <span className="shimmer">Thinking...</span>
              <span>{elapsedSeconds}s</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${Math.min(95, (1 - Math.exp(-(elapsedSeconds || 0) / 60)) * 100)}%` }}
              />
            </div>
          </div>
        ) : msg.isStreaming ? (
          <span>{msg.text}</span>
        ) : msg.role === 'assistant' ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
        ) : (
          msg.text
        )}
      </div>
      {!msg.isStreaming && msg.role === 'assistant' && msg.elapsedMs && (
        <div className="msg-footer">
          <span className="elapsed">
            {(msg.elapsedMs / 1000).toFixed(1)}s
            {msg.tokenCount && ` · ${(msg.tokenCount / (msg.elapsedMs / 1000)).toFixed(1)} tok/s`}
          </span>
          <button className="copy-btn" onClick={() => onCopy(msg.text)}>
            Copy
          </button>
        </div>
      )}
    </div>
  )
})

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const startTimeRef = useRef<number | null>(null)

  // Health check polling
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`)
        const data = await res.json()
        setHealth(data)
      } catch {
        setHealth(null)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 3000)
    return () => clearInterval(interval)
  }, [])

  // Focus input on mount and when health becomes ready
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    if (health?.ready) {
      inputRef.current?.focus()
    }
  }, [health?.ready])

  // Auto-scroll
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Timer for elapsed seconds
  useEffect(() => {
    if (!isGenerating) {
      setElapsedSeconds(0)
      return
    }

    const interval = setInterval(() => {
      if (startTimeRef.current) {
        setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [isGenerating])

  const sendMessage = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim() || isGenerating || !health?.ready) return

    setIsGenerating(true)
    startTimeRef.current = Date.now()
    setElapsedSeconds(0)

    const userMessage: Message = {
      id: Date.now(),
      text: messageText,
      role: 'user',
    }

    const assistantId = Date.now() + 1
    const assistantMessage: Message = {
      id: assistantId,
      text: '',
      role: 'assistant',
      isStreaming: true,
    }

    setMessages(prev => [...prev, userMessage, assistantMessage])
    setInput('')

    const requestStart = Date.now()
    let fullText = ''
    let tokenCount = 0

    try {
      const chatMessages: { role: string; content: string }[] = [
        {
          role: 'system',
          content: 'You are a friendly assistant. Be concise. When using markdown, ensure all formatting is complete - close all **bold**, *italic*, and ``` code blocks properly. Separate code from explanations.'
        }
      ]

      // Add conversation history
      messages
        .filter(m => !m.isStreaming)
        .forEach(m => chatMessages.push({ role: m.role, content: m.text }))
      chatMessages.push({ role: 'user', content: messageText })

      const res = await fetch(`${API_BASE}/v1/chat/completions`, {
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
            if (content) {
              fullText += content
              tokenCount++

              setMessages(prev => prev.map(msg =>
                msg.id === assistantId
                  ? { ...msg, text: fullText }
                  : msg
              ))
            }
          } catch {}
        }
      }

      const elapsedMs = Date.now() - requestStart
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, isStreaming: false, elapsedMs, tokenCount }
          : msg
      ))
    } catch (e) {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantId
          ? { ...msg, text: `Error: ${e instanceof Error ? e.message : 'Unknown'}`, isStreaming: false }
          : msg
      ))
    }

    setIsGenerating(false)
    startTimeRef.current = null
    inputRef.current?.focus()
  }

  const clearChat = () => {
    setMessages([])
  }

  const copyToClipboard = useCallback((text: string) => {
    navigator.clipboard.writeText(text)
  }, [])

  const getStatusClass = () => {
    if (!health) return 'error'
    if (!health.ready) return 'loading'
    return ''
  }

  const getStatusText = () => {
    if (!health) return 'Connecting...'
    if (!health.ready) {
      const stage = health.stage
      if (stage === 'downloading') return 'Downloading...'
      if (stage === 'loading') return 'Loading GPU...'
      return 'Starting...'
    }
    return health.model.split('/').pop() || 'Ready'
  }

  const getPlaceholder = () => {
    if (!health?.ready) return 'Loading model...'
    if (isGenerating) return 'Generating...'
    return 'Ask anything...'
  }

  return (
    <main>
      {/* Header */}
      <div className="header">
        <div className="header-left">
          <span className={`status-dot ${getStatusClass()}`} />
          <span className="model-name">{getStatusText()}</span>
        </div>
        {messages.length > 0 && (
          <button className="clear-btn" onClick={clearChat}>
            Clear chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h1>vmux Chat</h1>
            <p>{health?.ready ? health.model.split('/').pop() : 'Loading model...'}</p>
          </div>
        ) : (
          messages.map(msg => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              elapsedSeconds={msg.isStreaming ? elapsedSeconds : undefined}
              onCopy={copyToClipboard}
            />
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
              disabled={isGenerating || !health?.ready}
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
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              className="input-field"
              disabled={!health?.ready}
            />
            {!input && (
              <div className="input-placeholder">
                {getPlaceholder()}
              </div>
            )}
          </div>
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={!input.trim() || isGenerating || !health?.ready}
          >
            ↑
          </button>
        </div>
      </div>
    </main>
  )
}
