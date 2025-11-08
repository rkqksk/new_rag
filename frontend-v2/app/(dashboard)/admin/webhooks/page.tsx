"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Webhook, Plus, Trash2, Send, CheckCircle, XCircle } from "lucide-react"
import { toast } from "sonner"

interface WebhookConfig {
  id: string
  name: string
  url: string
  events: string[]
  enabled: boolean
  secret?: string
  retry_count: number
  timeout_ms: number
  created_at: string
}

interface WebhookLog {
  id: string
  webhook_id: string
  event: string
  status: "success" | "failed"
  response_code?: number
  response_time_ms?: number
  error?: string
  timestamp: string
}

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([
    {
      id: "wh_1",
      name: "Slack Notification",
      url: "https://hooks.slack.com/services/xxx",
      events: ["crawl_completed", "crawl_failed"],
      enabled: true,
      retry_count: 3,
      timeout_ms: 5000,
      created_at: "2025-11-01T10:00:00Z",
    },
    {
      id: "wh_2",
      name: "Custom API",
      url: "https://api.example.com/webhooks",
      events: ["crawl_completed"],
      enabled: true,
      secret: "sk_test_123",
      retry_count: 3,
      timeout_ms: 10000,
      created_at: "2025-11-05T14:30:00Z",
    },
  ])

  const [logs, setLogs] = useState<WebhookLog[]>([
    {
      id: "log_1",
      webhook_id: "wh_1",
      event: "crawl_completed",
      status: "success",
      response_code: 200,
      response_time_ms: 234,
      timestamp: "2025-11-08T10:30:00Z",
    },
    {
      id: "log_2",
      webhook_id: "wh_1",
      event: "crawl_completed",
      status: "success",
      response_code: 200,
      response_time_ms: 189,
      timestamp: "2025-11-08T09:15:00Z",
    },
    {
      id: "log_3",
      webhook_id: "wh_2",
      event: "crawl_failed",
      status: "failed",
      response_code: 500,
      error: "Internal Server Error",
      timestamp: "2025-11-07T18:45:00Z",
    },
  ])

  const [showAddForm, setShowAddForm] = useState(false)
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    url: "",
    events: [] as string[],
    secret: "",
  })

  const handleToggleWebhook = (id: string) => {
    setWebhooks((prev) =>
      prev.map((w) => (w.id === id ? { ...w, enabled: !w.enabled } : w))
    )
    const webhook = webhooks.find((w) => w.id === id)
    if (webhook) {
      toast.success(`Webhook이 ${!webhook.enabled ? "활성화" : "비활성화"}되었습니다`)
    }
  }

  const handleDeleteWebhook = (id: string) => {
    setWebhooks((prev) => prev.filter((w) => w.id !== id))
    toast.success("Webhook이 삭제되었습니다")
  }

  const handleTestWebhook = async (webhook: WebhookConfig) => {
    toast.info("테스트 전송 중...")
    // Simulate API call
    setTimeout(() => {
      const success = Math.random() > 0.3
      if (success) {
        toast.success(`테스트 성공! (${Math.floor(Math.random() * 300 + 100)}ms)`)
        const newLog: WebhookLog = {
          id: `log_${Date.now()}`,
          webhook_id: webhook.id,
          event: "test",
          status: "success",
          response_code: 200,
          response_time_ms: Math.floor(Math.random() * 300 + 100),
          timestamp: new Date().toISOString(),
        }
        setLogs((prev) => [newLog, ...prev])
      } else {
        toast.error("테스트 실패: Timeout")
        const newLog: WebhookLog = {
          id: `log_${Date.now()}`,
          webhook_id: webhook.id,
          event: "test",
          status: "failed",
          error: "Request timeout",
          timestamp: new Date().toISOString(),
        }
        setLogs((prev) => [newLog, ...prev])
      }
    }, 2000)
  }

  const handleAddWebhook = () => {
    const id = `wh_${Date.now()}`
    const webhook: WebhookConfig = {
      id,
      name: newWebhook.name,
      url: newWebhook.url,
      events: newWebhook.events,
      enabled: true,
      secret: newWebhook.secret || undefined,
      retry_count: 3,
      timeout_ms: 5000,
      created_at: new Date().toISOString(),
    }
    setWebhooks((prev) => [...prev, webhook])
    setShowAddForm(false)
    setNewWebhook({ name: "", url: "", events: [], secret: "" })
    toast.success("Webhook이 추가되었습니다!")
  }

  const toggleEvent = (event: string) => {
    setNewWebhook((prev) => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter((e) => e !== event)
        : [...prev.events, event],
    }))
  }

  const stats = {
    total: webhooks.length,
    active: webhooks.filter((w) => w.enabled).length,
    successRate:
      logs.length > 0
        ? Math.round((logs.filter((l) => l.status === "success").length / logs.length) * 100)
        : 0,
    totalCalls: logs.length,
  }

  return (
    <div className="space-y-6 p-6">
      <Navbar title="Webhook 관리" subtitle="Event Notifications & Integrations" />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="전체 Webhook" value={stats.total} icon="🔔" />
        <StatCard title="활성 Webhook" value={stats.active} icon="✅" changeType="neutral" />
        <StatCard title="성공률" value={`${stats.successRate}%`} icon="📊" changeType="neutral" />
        <StatCard title="전체 호출" value={stats.totalCalls} icon="📞" changeType="neutral" />
      </div>

      {/* Add Webhook Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-stone-100">새 Webhook 추가</CardTitle>
            <CardDescription className="text-stone-400">
              이벤트 발생 시 자동으로 호출될 Webhook을 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-stone-300">
                Webhook 이름
              </Label>
              <Input
                id="name"
                placeholder="예: Slack Notification"
                value={newWebhook.name}
                onChange={(e) => setNewWebhook((prev) => ({ ...prev, name: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="url" className="text-stone-300">
                Webhook URL
              </Label>
              <Input
                id="url"
                type="url"
                placeholder="https://hooks.slack.com/services/xxx"
                value={newWebhook.url}
                onChange={(e) => setNewWebhook((prev) => ({ ...prev, url: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-stone-300">이벤트 선택</Label>
              <div className="space-y-2">
                {[
                  { id: "crawl_completed", label: "크롤링 완료" },
                  { id: "crawl_failed", label: "크롤링 실패" },
                  { id: "crawl_started", label: "크롤링 시작" },
                  { id: "source_added", label: "소스 추가" },
                ].map((event) => (
                  <div key={event.id} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={event.id}
                      checked={newWebhook.events.includes(event.id)}
                      onChange={() => toggleEvent(event.id)}
                      className="h-4 w-4"
                    />
                    <Label htmlFor={event.id} className="text-stone-300 cursor-pointer">
                      {event.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="secret" className="text-stone-300">
                Secret (선택사항)
              </Label>
              <Input
                id="secret"
                type="password"
                placeholder="Webhook secret key"
                value={newWebhook.secret}
                onChange={(e) => setNewWebhook((prev) => ({ ...prev, secret: e.target.value }))}
              />
              <p className="text-xs text-stone-500">서명 검증에 사용됩니다</p>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleAddWebhook} disabled={!newWebhook.name || !newWebhook.url} className="flex-1">
                <Plus className="mr-2 h-4 w-4" />
                Webhook 추가
              </Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)} className="flex-1">
                취소
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Webhooks Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-stone-100">Webhook 목록</CardTitle>
              <CardDescription className="text-stone-400">
                등록된 Webhook ({webhooks.length}개)
              </CardDescription>
            </div>
            {!showAddForm && (
              <Button onClick={() => setShowAddForm(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Webhook 추가
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-stone-900 hover:bg-stone-950">
                <TableHead className="text-stone-400">이름</TableHead>
                <TableHead className="text-stone-400">URL</TableHead>
                <TableHead className="text-stone-400">이벤트</TableHead>
                <TableHead className="text-stone-400">상태</TableHead>
                <TableHead className="text-stone-400">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {webhooks.map((webhook) => (
                <TableRow key={webhook.id} className="border-stone-900 hover:bg-stone-950">
                  <TableCell className="text-stone-100">{webhook.name}</TableCell>
                  <TableCell className="text-stone-400 max-w-xs truncate">{webhook.url}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {webhook.events.map((event) => (
                        <Badge key={event} variant="outline" className="text-xs">
                          {event.replace("_", " ")}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={webhook.enabled}
                        onCheckedChange={() => handleToggleWebhook(webhook.id)}
                      />
                      <Badge variant={webhook.enabled ? "success" : "secondary"}>
                        {webhook.enabled ? "활성" : "비활성"}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTestWebhook(webhook)}
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Webhook 삭제</AlertDialogTitle>
                            <AlertDialogDescription>
                              정말 이 Webhook을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>취소</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteWebhook(webhook.id)}
                              className="bg-red-900 text-red-100 hover:bg-red-800"
                            >
                              삭제
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Webhook Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-stone-100">최근 호출 기록</CardTitle>
          <CardDescription className="text-stone-400">
            최근 Webhook 호출 결과 ({logs.length}건)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-stone-900 hover:bg-stone-950">
                <TableHead className="text-stone-400">시간</TableHead>
                <TableHead className="text-stone-400">Webhook</TableHead>
                <TableHead className="text-stone-400">이벤트</TableHead>
                <TableHead className="text-stone-400">상태</TableHead>
                <TableHead className="text-stone-400">응답 코드</TableHead>
                <TableHead className="text-stone-400">응답 시간</TableHead>
                <TableHead className="text-stone-400">에러</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.slice(0, 10).map((log) => {
                const webhook = webhooks.find((w) => w.id === log.webhook_id)
                return (
                  <TableRow key={log.id} className="border-stone-900 hover:bg-stone-950">
                    <TableCell className="text-stone-400">
                      {new Date(log.timestamp).toLocaleString("ko-KR")}
                    </TableCell>
                    <TableCell className="text-stone-100">{webhook?.name || "Unknown"}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{log.event}</Badge>
                    </TableCell>
                    <TableCell>
                      {log.status === "success" ? (
                        <CheckCircle className="h-5 w-5 text-green-400" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-400" />
                      )}
                    </TableCell>
                    <TableCell className="text-stone-400">
                      {log.response_code || "-"}
                    </TableCell>
                    <TableCell className="text-stone-400">
                      {log.response_time_ms ? `${log.response_time_ms}ms` : "-"}
                    </TableCell>
                    <TableCell className="text-red-400 max-w-xs truncate">
                      {log.error || "-"}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
