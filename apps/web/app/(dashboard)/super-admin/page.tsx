"use client"

import { useEffect, useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface DashboardStats {
  total_users: number
  api_calls: number
  active_sessions: number
  system_status: string
  users_change: string
  api_change: string
  sessions_change: number
}

interface SystemResource {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_usage: number
}

interface RecentActivity {
  user: string
  action: string
  timestamp: string
  type: "success" | "info" | "warning"
}

export default function SuperAdminPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [resources, setResources] = useState<SystemResource | null>(null)
  const [activities, setActivities] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch dashboard stats from real backend API
        const statsResponse = await fetch('http://localhost:8001/api/v1/dashboard/stats')
        if (statsResponse.ok) {
          const statsData = await statsResponse.json()
          setStats(statsData)
        }

        // Fetch system resources
        const resourcesResponse = await fetch('http://localhost:8001/api/v1/dashboard/performance')
        if (resourcesResponse.ok) {
          const resourcesData = await resourcesResponse.json()
          setResources(resourcesData)
        }

        // Fetch recent activities
        const activitiesResponse = await fetch('http://localhost:8001/api/v1/dashboard/documents?limit=4')
        if (activitiesResponse.ok) {
          const activitiesData = await activitiesResponse.json()
          // Transform backend data to activity format
          setActivities(activitiesData.items?.slice(0, 4).map((item: any) => ({
            user: item.user || 'system',
            action: item.title || item.action,
            timestamp: item.created_at || item.timestamp,
            type: item.status === 'success' ? 'success' : item.status === 'failed' ? 'warning' : 'info'
          })) || [])
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Fallback to mock data if API fails
        setStats({
          total_users: 0,
          api_calls: 0,
          active_sessions: 0,
          system_status: '연결 실패',
          users_change: '0%',
          api_change: '0%',
          sessions_change: 0
        })
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div>
        <Navbar title="시스템 개요" subtitle="전체 시스템 현황 및 모니터링" />
        <div className="p-6">
          <div className="text-center text-stone-400">데이터 로딩 중...</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <Navbar title="시스템 개요" subtitle="전체 시스템 현황 및 모니터링" />

      <div className="p-6 space-y-6">
        {/* Stats Grid - Real Backend Data */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="총 사용자"
            value={stats?.total_users?.toLocaleString() || '0'}
            change={stats?.users_change || '0%'}
            changeType={stats?.users_change?.includes('+') ? "increase" : "neutral"}
          />
          <StatCard
            title="API 호출"
            value={stats?.api_calls ? `${(stats.api_calls / 1000).toFixed(1)}K` : '0'}
            change={stats?.api_change || '0%'}
            changeType={stats?.api_change?.includes('+') ? "increase" : "neutral"}
          />
          <StatCard
            title="활성 세션"
            value={stats?.active_sessions || 0}
            change={stats?.sessions_change ? `${stats.sessions_change > 0 ? '+' : ''}${stats.sessions_change}` : '0'}
            changeType={stats?.sessions_change && stats.sessions_change > 0 ? "increase" : stats?.sessions_change && stats.sessions_change < 0 ? "decrease" : "neutral"}
          />
          <StatCard
            title="시스템 상태"
            value={stats?.system_status || '점검 중'}
            subtitle={stats?.system_status === '정상' ? '모든 서비스 운영 중' : '연결 확인 중'}
          />
        </div>

        {/* Recent Activity - Real Backend Data */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>최근 활동</CardTitle>
              <CardDescription>최근 24시간 동안의 시스템 활동</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {activities.length > 0 ? (
                  activities.map((activity, i) => (
                    <div key={i} className="flex items-center gap-3 rounded-lg bg-stone-950 p-3">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-stone-100">{activity.action}</p>
                        <p className="text-xs text-stone-500">{activity.user}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={activity.type === "success" ? "default" : activity.type === "warning" ? "destructive" : "secondary"}>
                          {activity.type}
                        </Badge>
                        <span className="text-xs text-stone-500">
                          {new Date(activity.timestamp).toLocaleTimeString('ko-KR')}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-stone-500 py-4">활동 내역 없음</div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>시스템 리소스</CardTitle>
              <CardDescription>서버 리소스 사용률</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { label: "CPU", value: resources?.cpu_usage || 0, color: "bg-stone-600" },
                  { label: "메모리", value: resources?.memory_usage || 0, color: "bg-stone-500" },
                  { label: "디스크", value: resources?.disk_usage || 0, color: "bg-stone-600" },
                  { label: "네트워크", value: resources?.network_usage || 0, color: "bg-stone-500" },
                ].map((resource) => (
                  <div key={resource.label}>
                    <div className="mb-2 flex items-center justify-between text-sm">
                      <span className="text-stone-400">{resource.label}</span>
                      <span className="text-stone-100">{resource.value}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className={`h-full ${resource.color} transition-all duration-500`}
                        style={{ width: `${resource.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* User Management Preview */}
        <Card>
          <CardHeader>
            <CardTitle>사용자 관리</CardTitle>
            <CardDescription>최근 등록된 사용자</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { name: "김철수", email: "kim@example.com", role: "admin", date: "2025-11-08" },
                { name: "이영희", email: "lee@example.com", role: "staff", date: "2025-11-07" },
                { name: "박민수", email: "park@example.com", role: "customer", date: "2025-11-07" },
                { name: "최지영", email: "choi@example.com", role: "customer-vip", date: "2025-11-06" },
              ].map((user, i) => (
                <div key={i} className="flex items-center gap-4 rounded-lg bg-stone-950 p-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-stone-800 text-stone-100">
                    {user.name.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-stone-100">{user.name}</p>
                    <p className="text-xs text-stone-500">{user.email}</p>
                  </div>
                  <Badge>{user.role}</Badge>
                  <span className="text-xs text-stone-500">{user.date}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
