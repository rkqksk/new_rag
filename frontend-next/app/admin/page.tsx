'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.API_URL || 'http://localhost:8001'

interface EngineHealth {
  healthy: boolean
  error?: string
}

interface Health {
  unified: boolean
  engines: {
    nexa?: EngineHealth
    ollama?: EngineHealth
  }
}

interface Stats {
  nexa_requests: number
  ollama_requests: number
  errors: number
  nexa_available: boolean
  ollama_available: boolean
}

interface ModelInfo {
  id: string
  created?: number
  owned_by?: string
}

export default function AdminPage() {
  const [health, setHealth] = useState<Health | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [routerConfig, setRouterConfig] = useState({
    simple_threshold: 0.3,
    complex_threshold: 0.7
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      // Fetch health
      const healthRes = await fetch(`${API_URL}/api/v1/admin/health`)
      const healthData = await healthRes.json()
      setHealth(healthData)

      // Fetch stats
      const statsRes = await fetch(`${API_URL}/api/v1/admin/stats`)
      const statsData = await statsRes.json()
      setStats(statsData)

      // Fetch models (if NexaAI is available)
      if (healthData.engines.nexa?.healthy) {
        const modelsRes = await fetch(`${API_URL}/api/v1/admin/models`)
        const modelsData = await modelsRes.json()
        setModels(modelsData)
      }

    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()

    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const updateRouterConfig = async () => {
    try {
      await fetch(`${API_URL}/api/v1/admin/router/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(routerConfig)
      })
      alert('설정이 업데이트되었습니다!')
    } catch (error) {
      alert('설정 업데이트 실패: ' + error)
    }
  }

  if (loading && !health) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="gradient-bg text-white py-6 shadow-lg">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold">⚙️ 관리자 페이지</h1>
          <p className="text-sm opacity-90 mt-1">시스템 모니터링 & 설정</p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* System Health */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">시스템 상태</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Overall Health */}
            <div className="card">
              <h3 className="font-semibold mb-2">전체 시스템</h3>
              <div className="flex items-center justify-between">
                <span className={`text-3xl ${health?.unified ? 'text-green-600' : 'text-red-600'}`}>
                  {health?.unified ? '✓' : '✗'}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  health?.unified ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {health?.unified ? '정상' : '오류'}
                </span>
              </div>
            </div>

            {/* NexaAI Health */}
            <div className="card">
              <h3 className="font-semibold mb-2">NexaAI 엔진</h3>
              <div className="flex items-center justify-between">
                <span className={`text-3xl ${health?.engines.nexa?.healthy ? 'text-green-600' : 'text-red-600'}`}>
                  {health?.engines.nexa?.healthy ? '✓' : '✗'}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  health?.engines.nexa?.healthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {health?.engines.nexa?.healthy ? '정상' : health?.engines.nexa?.error || '오류'}
                </span>
              </div>
            </div>

            {/* Ollama Health */}
            <div className="card">
              <h3 className="font-semibold mb-2">Ollama 엔진</h3>
              <div className="flex items-center justify-between">
                <span className={`text-3xl ${health?.engines.ollama?.healthy ? 'text-green-600' : 'text-red-600'}`}>
                  {health?.engines.ollama?.healthy ? '✓' : '✗'}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  health?.engines.ollama?.healthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {health?.engines.ollama?.healthy ? '정상' : health?.engines.ollama?.error || '오류'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">통계</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold text-blue-600">{stats?.nexa_requests || 0}</p>
              <p className="text-sm text-gray-600 mt-1">NexaAI 요청</p>
            </div>

            <div className="card text-center">
              <p className="text-3xl font-bold text-purple-600">{stats?.ollama_requests || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Ollama 요청</p>
            </div>

            <div className="card text-center">
              <p className="text-3xl font-bold text-green-600">
                {stats ? stats.nexa_requests + stats.ollama_requests : 0}
              </p>
              <p className="text-sm text-gray-600 mt-1">총 요청</p>
            </div>

            <div className="card text-center">
              <p className="text-3xl font-bold text-red-600">{stats?.errors || 0}</p>
              <p className="text-sm text-gray-600 mt-1">오류</p>
            </div>
          </div>
        </div>

        {/* Models */}
        {models.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">사용 가능한 모델</h2>

            <div className="card">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">모델 ID</th>
                      <th className="text-left py-2 px-4">소유자</th>
                      <th className="text-left py-2 px-4">생성 날짜</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.map((model, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-2 px-4 font-mono text-sm">{model.id}</td>
                        <td className="py-2 px-4">{model.owned_by || 'N/A'}</td>
                        <td className="py-2 px-4">
                          {model.created ? new Date(model.created * 1000).toLocaleDateString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Router Configuration */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">라우터 설정</h2>

          <div className="card">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-2">
                  Simple Threshold (단순 쿼리 임계값)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={routerConfig.simple_threshold}
                  onChange={(e) => setRouterConfig({
                    ...routerConfig,
                    simple_threshold: parseFloat(e.target.value)
                  })}
                  className="input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  이 값보다 낮으면 빠른 모델(NexaAI Qwen3-1.7B) 사용
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">
                  Complex Threshold (복잡한 쿼리 임계값)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={routerConfig.complex_threshold}
                  onChange={(e) => setRouterConfig({
                    ...routerConfig,
                    complex_threshold: parseFloat(e.target.value)
                  })}
                  className="input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  이 값보다 높으면 고품질 모델(Ollama qwen2.5:7b) 사용
                </p>
              </div>
            </div>

            <button
              onClick={updateRouterConfig}
              className="btn-primary mt-4"
            >
              설정 저장
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">액션</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={fetchData}
              className="card hover:shadow-lg transition-shadow cursor-pointer text-center py-4"
            >
              <span className="text-2xl mb-2 block">🔄</span>
              <span className="font-semibold">데이터 새로고침</span>
            </button>

            <a
              href={`${API_URL}/api/v1/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="card hover:shadow-lg transition-shadow cursor-pointer text-center py-4"
            >
              <span className="text-2xl mb-2 block">📚</span>
              <span className="font-semibold">API 문서</span>
            </a>

            <a
              href="/"
              className="card hover:shadow-lg transition-shadow cursor-pointer text-center py-4"
            >
              <span className="text-2xl mb-2 block">🏠</span>
              <span className="font-semibold">메인 페이지</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
