'use client'

import { useState } from 'react'

const API_URL = process.env.API_URL || 'http://localhost:8001'

interface Message {
  role: 'user' | 'assistant'
  content: string
  routing?: {
    engine: string
    model: string
    reason: string
  }
}

interface Product {
  id: string
  name: string
  code: string
  capacity?: string
  material?: string
  score: number
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [sessionId] = useState(() => `session-${Date.now()}`)

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/v1/chat/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          session_id: sessionId,
          top_k: 3
        })
      })

      if (!response.ok) throw new Error('API request failed')

      const data = await response.json()

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer || data.response,
        routing: data.routing
      }

      setMessages(prev => [...prev, assistantMessage])

      if (data.products) {
        setProducts(data.products)
      }

    } catch (error) {
      console.error('Error:', error)

      const errorMessage: Message = {
        role: 'assistant',
        content: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.'
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="gradient-bg text-white py-6 shadow-lg">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold">🏠 RAG Enterprise</h1>
          <p className="text-sm opacity-90 mt-1">NexaAI + Qdrant로 구동되는 스마트 제품 검색</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Chat Area */}
          <div className="lg:col-span-2 card flex flex-col" style={{ height: '70vh' }}>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto mb-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 mt-12">
                  <p className="text-lg mb-2">안녕하세요! 👋</p>
                  <p>제품을 검색해보세요.</p>
                  <div className="mt-4 flex flex-wrap gap-2 justify-center">
                    {['50ml PET 용기', '100ml 투명 용기', '24파이 캡'].map(example => (
                      <button
                        key={example}
                        onClick={() => setInput(example)}
                        className="px-4 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200 transition-colors"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-primary to-secondary text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>

                    {msg.routing && (
                      <div className="mt-2 text-xs opacity-75">
                        <span className="bg-white/20 px-2 py-1 rounded">
                          {msg.routing.engine} / {msg.routing.model}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-4 py-3 rounded-lg">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="제품을 검색하세요..."
                className="input flex-1"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="btn-primary px-6"
              >
                전송
              </button>
            </div>
          </div>

          {/* Products Sidebar */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4">추천 제품</h2>

            {products.length === 0 ? (
              <div className="text-center text-gray-400 py-12">
                <p>제품을 검색하면</p>
                <p>추천 제품이 표시됩니다</p>
              </div>
            ) : (
              <div className="space-y-3">
                {products.map((product, idx) => (
                  <div
                    key={product.id || idx}
                    className="border-2 border-gray-100 rounded-lg p-3 hover:border-primary transition-colors cursor-pointer"
                  >
                    <h3 className="font-semibold text-sm">{product.name}</h3>
                    {product.code && (
                      <p className="text-xs text-gray-500 mt-1">코드: {product.code}</p>
                    )}
                    {product.capacity && (
                      <p className="text-xs text-gray-600 mt-1">용량: {product.capacity}</p>
                    )}
                    {product.material && (
                      <p className="text-xs text-gray-600">재질: {product.material}</p>
                    )}
                    <div className="mt-2">
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                        유사도: {(product.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="card text-center">
            <p className="text-2xl font-bold text-primary">{messages.length}</p>
            <p className="text-sm text-gray-600">메시지</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-primary">{products.length}</p>
            <p className="text-sm text-gray-600">추천 제품</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-green-600">NexaAI</p>
            <p className="text-sm text-gray-600">AI 엔진</p>
          </div>
          <div className="card text-center">
            <p className="text-2xl font-bold text-blue-600">Qdrant</p>
            <p className="text-sm text-gray-600">벡터 DB</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600">
          <p>Powered by NexaAI SDK + Qdrant + FastAPI</p>
          <p className="mt-1">
            <a href="/admin" className="text-primary hover:underline">관리자 페이지</a>
            {' • '}
            <a href={`${API_URL}/api/v1/docs`} target="_blank" rel="noopener" className="text-primary hover:underline">
              API 문서
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
