"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
interface ApiKey {
  id: string
  name: string
  key: string
  created: string
  lastUsed: string
  calls: string
  limit: string
  status: "active" | "inactive"
}

export default function ApiKeysPage() {
  const [showKey, setShowKey] = useState<{ [key: string]: boolean }>({})
  const [apiKeys] = useState<ApiKey[]>([
    {
      id: "1",
      name: "Production API",
      key: "pk_live_1234567890abcdef1234567890abcdef",
      created: "2024-01-15",
      lastUsed: "2025-11-11 14:23",
      calls: "124500",
      limit: "500000",
      status: "active",
    },
    {
      id: "2",
      name: "Development API",
      key: "pk_dev_abcdef1234567890abcdef1234567890",
      created: "2024-03-20",
      lastUsed: "2025-11-11 12:15",
      calls: "32400",
      limit: "100000",
      status: "active",
    },
    {
      id: "3",
      name: "Test API",
      key: "pk_test_xyz1234567890abcdef1234567890abc",
      created: "2024-06-10",
      lastUsed: "2025-11-08 09:30",
      calls: "8920",
      limit: "50000",
      status: "active",
    },
    {
      id: "4",
      name: "Legacy API",
      key: "pk_old_1234567890abcdef1234567890abcdef",
      created: "2023-11-01",
      lastUsed: "2025-10-15 16:45",
      calls: "0",
      limit: "50000",
      status: "inactive",
    },
  ])

  const toggleKeyVisibility = (id: string) => {
    setShowKey((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const maskKey = (key: string) => {
    return key.substring(0, 8) + "•".repeat(24) + key.substring(key.length - 4)
  }

  const calculateUsagePercentage = (calls: string, limit: string) => {
    return (parseInt(calls) / parseInt(limit)) * 100
  }

  return (
    <div>
      <Navbar title="API 키 관리" subtitle="API 키 및 사용량 모니터링" />

      <div className="p-6 space-y-6">
        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  Key
                </div>
                <div>
                  <p className="text-xs text-stone-400">총 API 키</p>
                  <p className="text-2xl font-bold text-stone-100">4</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  Activity
                </div>
                <div>
                  <p className="text-xs text-stone-400">활성 키</p>
                  <p className="text-2xl font-bold text-stone-100">3</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div>
                <p className="text-xs text-stone-400">총 API 호출</p>
                <p className="text-2xl font-bold text-stone-100">165.8K</p>
                <p className="text-xs text-stone-500 mt-1">이번 달</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div>
                <p className="text-xs text-stone-400">평균 응답 시간</p>
                <p className="text-2xl font-bold text-stone-100">245ms</p>
                <p className="text-xs text-stone-500 mt-1">지난 24시간</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* API Keys List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>API 키 목록</CardTitle>
                <CardDescription>등록된 API 키 및 사용 현황</CardDescription>
              </div>
              <Button>
                +
                새 키 생성
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {apiKeys.map((apiKey) => (
                <div
                  key={apiKey.id}
                  className="rounded-lg border border-stone-800 bg-stone-950 p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-stone-100">{apiKey.name}</h3>
                        <Badge
                          variant={apiKey.status === "active" ? "default" : "outline"}
                          className={
                            apiKey.status === "active"
                              ? "bg-stone-700 text-stone-100"
                              : "bg-stone-900 text-stone-400"
                          }
                        >
                          {apiKey.status === "active" ? "활성" : "비활성"}
                        </Badge>
                      </div>

                      <div className="mb-3 flex items-center gap-2">
                        <code className="flex-1 rounded bg-stone-900 px-3 py-2 font-mono text-xs text-stone-300">
                          {showKey[apiKey.id] ? apiKey.key : maskKey(apiKey.key)}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleKeyVisibility(apiKey.id)}
                        >
                          {showKey[apiKey.id] ? (
                            Hide
                          ) : (
                            Show
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(apiKey.key)}
                        >
                          Copy
                        </Button>
                      </div>

                      <div className="mb-3 grid gap-2 md:grid-cols-2">
                        <div className="text-xs">
                          <span className="text-stone-500">생성일: </span>
                          <span className="text-stone-300">{apiKey.created}</span>
                        </div>
                        <div className="text-xs">
                          <span className="text-stone-500">마지막 사용: </span>
                          <span className="text-stone-300">{apiKey.lastUsed}</span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-stone-400">사용량</span>
                          <span className="text-stone-300">
                            {parseInt(apiKey.calls).toLocaleString()} / {parseInt(apiKey.limit).toLocaleString()} 호출
                          </span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                          <div
                            className="h-full bg-stone-700 transition-all duration-500"
                            style={{
                              width: `${calculateUsagePercentage(apiKey.calls, apiKey.limit)}%`,
                            }}
                          />
                        </div>
                        <div className="flex justify-end text-xs text-stone-500">
                          {calculateUsagePercentage(apiKey.calls, apiKey.limit).toFixed(1)}% 사용됨
                        </div>
                      </div>
                    </div>

                    <Button variant="ghost" size="sm" className="text-stone-400 hover:text-stone-100">
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Rate Limits */}
        <Card>
          <CardHeader>
            <CardTitle>Rate Limit 설정</CardTitle>
            <CardDescription>API 호출 제한 및 속도 제어</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { endpoint: "POST /api/v1/hybrid/search", limit: "100 req/min", current: "45 req/min" },
                { endpoint: "GET /api/v1/documents", limit: "200 req/min", current: "82 req/min" },
                { endpoint: "POST /api/v1/embed", limit: "50 req/min", current: "23 req/min" },
              ].map((rate, idx) => (
                <div key={idx} className="rounded-lg bg-stone-950 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <code className="text-xs text-stone-300">{rate.endpoint}</code>
                    <Badge variant="outline" className="bg-stone-800 text-stone-300 font-mono text-xs">
                      {rate.limit}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                        <div
                          className="h-full bg-stone-700"
                          style={{
                            width: `${(parseInt(rate.current) / parseInt(rate.limit)) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <span className="text-xs text-stone-400 w-24 text-right">{rate.current}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Usage Statistics */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>주간 호출 추이</CardTitle>
              <CardDescription>최근 7일 API 호출 현황</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[200px] flex items-end justify-around gap-2">
                {[
                  { day: "월", value: 65 },
                  { day: "화", value: 82 },
                  { day: "수", value: 75 },
                  { day: "목", value: 90 },
                  { day: "금", value: 95 },
                  { day: "토", value: 45 },
                  { day: "일", value: 38 },
                ].map((data) => (
                  <div key={data.day} className="flex flex-col items-center gap-2 flex-1">
                    <div className="relative w-full">
                      <div
                        className="w-full bg-stone-700 rounded-t-lg transition-all duration-500 hover:bg-stone-600"
                        style={{ height: `${data.value * 2}px` }}
                      />
                    </div>
                    <span className="text-xs text-stone-400">{data.day}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>엔드포인트별 사용량</CardTitle>
              <CardDescription>API 엔드포인트 호출 분포</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { endpoint: "/hybrid/search", percentage: 45, calls: "74.5K" },
                  { endpoint: "/documents", percentage: 30, calls: "49.7K" },
                  { endpoint: "/embed", percentage: 15, calls: "24.9K" },
                  { endpoint: "/health", percentage: 10, calls: "16.6K" },
                ].map((item) => (
                  <div key={item.endpoint} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <code className="text-stone-300">{item.endpoint}</code>
                      <div className="flex items-center gap-2">
                        <span className="text-stone-400 text-xs">{item.calls}</span>
                        <span className="text-stone-500 text-xs w-10 text-right">{item.percentage}%</span>
                      </div>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className="h-full bg-stone-700 transition-all duration-500"
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
