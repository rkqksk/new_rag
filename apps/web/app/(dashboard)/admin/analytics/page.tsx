"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TrendingUp, TrendingDown, Activity, Zap, Clock, AlertTriangle } from "lucide-react"
import { useSorting } from "@/hooks/useSorting"

interface APIUsage {
  endpoint: string
  method: string
  calls: number
  avg_response_time: number
  error_rate: number
  last_called: string
}

interface UsageByDay {
  date: string
  total_calls: number
  successful_calls: number
  failed_calls: number
  avg_response_time: number
}

interface TopUser {
  user_id: string
  user_name: string
  total_calls: number
  endpoints_used: number
  last_active: string
}

// Mock data
const mockEndpoints: APIUsage[] = [
  {
    endpoint: "/api/v1/search",
    method: "POST",
    calls: 15420,
    avg_response_time: 245,
    error_rate: 0.8,
    last_called: "2025-11-08T14:30:00Z"
  },
  {
    endpoint: "/api/v1/ingestion/crawler/start",
    method: "POST",
    calls: 8750,
    avg_response_time: 1850,
    error_rate: 2.3,
    last_called: "2025-11-08T14:28:00Z"
  },
  {
    endpoint: "/api/v1/ingestion/crawler/sources",
    method: "GET",
    calls: 12340,
    avg_response_time: 120,
    error_rate: 0.2,
    last_called: "2025-11-08T14:29:00Z"
  },
  {
    endpoint: "/api/v1/admin/stats",
    method: "GET",
    calls: 6820,
    avg_response_time: 95,
    error_rate: 0.1,
    last_called: "2025-11-08T14:25:00Z"
  },
  {
    endpoint: "/api/v1/recommendations",
    method: "POST",
    calls: 4560,
    avg_response_time: 380,
    error_rate: 1.5,
    last_called: "2025-11-08T14:20:00Z"
  },
]

const mockDailyUsage: UsageByDay[] = [
  { date: "2025-11-01", total_calls: 45200, successful_calls: 44100, failed_calls: 1100, avg_response_time: 250 },
  { date: "2025-11-02", total_calls: 48500, successful_calls: 47200, failed_calls: 1300, avg_response_time: 265 },
  { date: "2025-11-03", total_calls: 42800, successful_calls: 41900, failed_calls: 900, avg_response_time: 230 },
  { date: "2025-11-04", total_calls: 51200, successful_calls: 49800, failed_calls: 1400, avg_response_time: 280 },
  { date: "2025-11-05", total_calls: 49700, successful_calls: 48500, failed_calls: 1200, avg_response_time: 270 },
  { date: "2025-11-06", total_calls: 46300, successful_calls: 45400, failed_calls: 900, avg_response_time: 245 },
  { date: "2025-11-07", total_calls: 53100, successful_calls: 51700, failed_calls: 1400, avg_response_time: 290 },
  { date: "2025-11-08", total_calls: 28600, successful_calls: 27900, failed_calls: 700, avg_response_time: 255 },
]

const mockTopUsers: TopUser[] = [
  {
    user_id: "user_1",
    user_name: "Admin User",
    total_calls: 18500,
    endpoints_used: 12,
    last_active: "2025-11-08T14:30:00Z"
  },
  {
    user_id: "user_2",
    user_name: "Manager User",
    total_calls: 12300,
    endpoints_used: 8,
    last_active: "2025-11-08T14:25:00Z"
  },
  {
    user_id: "user_3",
    user_name: "Staff User",
    total_calls: 8700,
    endpoints_used: 5,
    last_active: "2025-11-08T14:20:00Z"
  },
  {
    user_id: "user_4",
    user_name: "Customer VIP",
    total_calls: 6200,
    endpoints_used: 4,
    last_active: "2025-11-08T14:15:00Z"
  },
  {
    user_id: "user_5",
    user_name: "Customer User",
    total_calls: 3800,
    endpoints_used: 3,
    last_active: "2025-11-08T14:10:00Z"
  },
]

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<string>("7d")

  // Sorting hooks
  const { sortedData: sortedEndpoints, handleSort: handleSortEndpoints, getSortIcon: getSortIconEndpoints }
    = useSorting(mockEndpoints, 'calls', 'desc')
  const { sortedData: sortedUsers, handleSort: handleSortUsers, getSortIcon: getSortIconUsers }
    = useSorting(mockTopUsers, 'total_calls', 'desc')

  // Calculate stats
  const totalCalls = mockDailyUsage.reduce((sum, day) => sum + day.total_calls, 0)
  const totalSuccess = mockDailyUsage.reduce((sum, day) => sum + day.successful_calls, 0)
  const totalFailed = mockDailyUsage.reduce((sum, day) => sum + day.failed_calls, 0)
  const avgResponseTime = Math.round(
    mockDailyUsage.reduce((sum, day) => sum + day.avg_response_time, 0) / mockDailyUsage.length
  )
  const successRate = ((totalSuccess / totalCalls) * 100).toFixed(1)

  // Get trend (compare last 2 days)
  const recentCalls = mockDailyUsage.slice(-2)
  const callsTrend = recentCalls.length === 2
    ? ((recentCalls[1].total_calls - recentCalls[0].total_calls) / recentCalls[0].total_calls * 100).toFixed(1)
    : "0"

  return (
    <div className="space-y-6 p-6">
      <Navbar
        title="사용량 분석"
        subtitle="API Usage & Analytics Dashboard"
      />

      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-stone-400">기간:</span>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">최근 24시간</SelectItem>
              <SelectItem value="7d">최근 7일</SelectItem>
              <SelectItem value="30d">최근 30일</SelectItem>
              <SelectItem value="90d">최근 90일</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="총 API 호출"
          value={totalCalls.toLocaleString()}

          subtitle={`${callsTrend}% vs. 전일`}
          changeType={parseFloat(callsTrend) >= 0 ? "increase" : "decrease"}
        />
        <StatCard
          title="성공률"
          value={`${successRate}%`}

          subtitle={`${totalSuccess.toLocaleString()} / ${totalCalls.toLocaleString()}`}
          changeType="increase"
        />
        <StatCard
          title="평균 응답 시간"
          value={`${avgResponseTime}ms`}
          
          subtitle="전체 엔드포인트 평균"
        />
        <StatCard
          title="에러율"
          value={`${((totalFailed / totalCalls) * 100).toFixed(2)}%`}

          subtitle={`${totalFailed.toLocaleString()} 실패`}
          changeType={totalFailed > 1000 ? "decrease" : "neutral"}
        />
      </div>

      <Tabs defaultValue="endpoints" className="space-y-4">
        <TabsList className="bg-stone-950">
          <TabsTrigger value="endpoints">엔드포인트 통계</TabsTrigger>
          <TabsTrigger value="daily">일별 사용량</TabsTrigger>
          <TabsTrigger value="users">사용자 통계</TabsTrigger>
        </TabsList>

        {/* Endpoints Tab */}
        <TabsContent value="endpoints" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">API 엔드포인트 통계</CardTitle>
              <CardDescription className="text-stone-400">
                엔드포인트별 호출 수, 응답 시간, 에러율
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortEndpoints('endpoint')}>
                      엔드포인트 {getSortIconEndpoints('endpoint')}
                    </TableHead>
                    <TableHead className="text-stone-400">메서드</TableHead>
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortEndpoints('calls')}>
                      호출 수 {getSortIconEndpoints('calls')}
                    </TableHead>
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortEndpoints('avg_response_time')}>
                      평균 응답시간 {getSortIconEndpoints('avg_response_time')}
                    </TableHead>
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortEndpoints('error_rate')}>
                      에러율 {getSortIconEndpoints('error_rate')}
                    </TableHead>
                    <TableHead className="text-stone-400">마지막 호출</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedEndpoints.map((endpoint) => (
                    <TableRow key={endpoint.endpoint} className="border-stone-900 hover:bg-stone-950">
                      <TableCell className="font-mono text-sm text-stone-100">
                        {endpoint.endpoint}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {endpoint.method}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-stone-100 font-medium">
                        {endpoint.calls.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-stone-500" />
                          <span className={`text-sm ${endpoint.avg_response_time > 1000 ? 'text-stone-400' : 'text-stone-300'}`}>
                            {endpoint.avg_response_time}ms
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {endpoint.error_rate > 2 ? (
                            <AlertTriangle className="h-4 w-4 text-stone-400" />
                          ) : null}
                          <span className={`text-sm ${endpoint.error_rate > 2 ? 'text-stone-400' : 'text-stone-300'}`}>
                            {endpoint.error_rate}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-stone-400 text-xs">
                        {new Date(endpoint.last_called).toLocaleString("ko-KR")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Response Time Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">응답 시간 분포</CardTitle>
              <CardDescription className="text-stone-400">
                엔드포인트별 응답 시간 시각화
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sortedEndpoints.map((endpoint) => {
                  const maxTime = Math.max(...mockEndpoints.map(e => e.avg_response_time))
                  const percentage = (endpoint.avg_response_time / maxTime) * 100

                  return (
                    <div key={endpoint.endpoint} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-stone-300 font-mono truncate max-w-xs">
                          {endpoint.endpoint}
                        </span>
                        <span className="text-stone-100 font-medium">
                          {endpoint.avg_response_time}ms
                        </span>
                      </div>
                      <div className="h-2 bg-stone-900 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            endpoint.avg_response_time > 1000
                              ? 'bg-stone-800'
                              : endpoint.avg_response_time > 500
                                ? 'bg-stone-700'
                                : 'bg-stone-600'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Daily Usage Tab */}
        <TabsContent value="daily" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">일별 API 사용량</CardTitle>
              <CardDescription className="text-stone-400">
                날짜별 호출 수 및 성공/실패 통계
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="text-stone-400">날짜</TableHead>
                    <TableHead className="text-stone-400">총 호출</TableHead>
                    <TableHead className="text-stone-400">성공</TableHead>
                    <TableHead className="text-stone-400">실패</TableHead>
                    <TableHead className="text-stone-400">성공률</TableHead>
                    <TableHead className="text-stone-400">평균 응답시간</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockDailyUsage.map((day) => {
                    const successRate = ((day.successful_calls / day.total_calls) * 100).toFixed(1)
                    const prevDay = mockDailyUsage[mockDailyUsage.indexOf(day) - 1]
                    const trend = prevDay
                      ? ((day.total_calls - prevDay.total_calls) / prevDay.total_calls * 100).toFixed(1)
                      : null

                    return (
                      <TableRow key={day.date} className="border-stone-900 hover:bg-stone-950">
                        <TableCell className="text-stone-100 font-medium">
                          {new Date(day.date).toLocaleDateString("ko-KR", {
                            month: "short",
                            day: "numeric",
                            weekday: "short"
                          })}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="text-stone-100 font-medium">
                              {day.total_calls.toLocaleString()}
                            </span>
                            {trend && (
                              <div className={`flex items-center gap-1 text-xs ${
                                parseFloat(trend) >= 0 ? 'text-stone-300' : 'text-stone-400'
                              }`}>
                                {parseFloat(trend) >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                                {Math.abs(parseFloat(trend))}%
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-stone-300">
                          {day.successful_calls.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-stone-400">
                          {day.failed_calls.toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant={parseFloat(successRate) >= 95 ? "default" : "destructive"}>
                            {successRate}%
                          </Badge>
                        </TableCell>
                        <TableCell className="text-stone-300">
                          {day.avg_response_time}ms
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Visual Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">호출 수 추이</CardTitle>
              <CardDescription className="text-stone-400">
                일별 API 호출 수 시각화
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {mockDailyUsage.map((day) => {
                  const maxCalls = Math.max(...mockDailyUsage.map(d => d.total_calls))
                  const percentage = (day.total_calls / maxCalls) * 100

                  return (
                    <div key={day.date} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-stone-400 w-24">
                          {new Date(day.date).toLocaleDateString("ko-KR", { month: "short", day: "numeric" })}
                        </span>
                        <span className="text-stone-100 font-medium">
                          {day.total_calls.toLocaleString()}
                        </span>
                      </div>
                      <div className="h-8 bg-stone-900 rounded overflow-hidden relative">
                        <div
                          className="h-full bg-stone-700 transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                        <div
                          className="absolute top-0 left-0 h-full bg-stone-600"
                          style={{ width: `${(day.successful_calls / maxCalls) * 100}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="mt-4 flex items-center gap-4 text-xs text-stone-400">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 bg-stone-700 rounded" />
                  <span>총 호출</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 bg-stone-600 rounded" />
                  <span>성공</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">Top 사용자</CardTitle>
              <CardDescription className="text-stone-400">
                가장 많이 API를 사용하는 사용자
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="text-stone-400">순위</TableHead>
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortUsers('user_name')}>
                      사용자 {getSortIconUsers('user_name')}
                    </TableHead>
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortUsers('total_calls')}>
                      총 호출 수 {getSortIconUsers('total_calls')}
                    </TableHead>
                    <TableHead className="text-stone-400 cursor-pointer" onClick={() => handleSortUsers('endpoints_used')}>
                      사용 엔드포인트 {getSortIconUsers('endpoints_used')}
                    </TableHead>
                    <TableHead className="text-stone-400">마지막 활동</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedUsers.map((user, index) => (
                    <TableRow key={user.user_id} className="border-stone-900 hover:bg-stone-950">
                      <TableCell>
                        <div className="flex items-center justify-center">
                          {index > 2 && <span className="text-stone-400">{index + 1}</span>}
                        </div>
                      </TableCell>
                      <TableCell className="text-stone-100 font-medium">
                        {user.user_name}
                      </TableCell>
                      <TableCell className="text-stone-100 font-medium">
                        {user.total_calls.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-stone-300">
                        {user.endpoints_used}개
                      </TableCell>
                      <TableCell className="text-stone-400 text-xs">
                        {new Date(user.last_active).toLocaleString("ko-KR")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
