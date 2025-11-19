"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { toast } from "sonner"

interface Schedule {
  id: string
  source_id: string
  source_name: string
  frequency: "hourly" | "daily" | "weekly" | "monthly" | "custom"
  cron_expression?: string
  timezone: string
  enabled: boolean
  next_run: string
  last_run: string | null
  created_at: string
}

export default function SchedulerPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([
    {
      id: "sched_1",
      source_id: "product_catalog",
      source_name: "Product Catalog",
      frequency: "daily",
      timezone: "Asia/Seoul",
      enabled: true,
      next_run: "2025-11-09T02:00:00Z",
      last_run: "2025-11-08T02:00:00Z",
      created_at: "2025-11-01T10:00:00Z",
    },
    {
      id: "sched_2",
      source_id: "msds_db",
      source_name: "MSDS Database",
      frequency: "weekly",
      timezone: "Asia/Seoul",
      enabled: true,
      next_run: "2025-11-15T00:00:00Z",
      last_run: "2025-11-08T00:00:00Z",
      created_at: "2025-11-01T10:00:00Z",
    },
    {
      id: "sched_3",
      source_id: "supplier_info",
      source_name: "Supplier Directory",
      frequency: "monthly",
      timezone: "Asia/Seoul",
      enabled: false,
      next_run: "2025-12-01T00:00:00Z",
      last_run: null,
      created_at: "2025-11-05T14:30:00Z",
    },
  ])

  const [showAddForm, setShowAddForm] = useState(false)
  const [newSchedule, setNewSchedule] = useState({
    source_id: "",
    frequency: "daily" as Schedule["frequency"],
    timezone: "Asia/Seoul",
    cron_expression: "",
  })

  const handleToggleSchedule = (id: string) => {
    setSchedules((prev) =>
      prev.map((s) =>
        s.id === id ? { ...s, enabled: !s.enabled } : s
      )
    )
    const schedule = schedules.find((s) => s.id === id)
    if (schedule) {
      toast.success(`스케줄이 ${!schedule.enabled ? "활성화" : "비활성화"}되었습니다`)
    }
  }

  const handleDeleteSchedule = (id: string) => {
    setSchedules((prev) => prev.filter((s) => s.id !== id))
    toast.success("스케줄이 삭제되었습니다")
  }

  const handleAddSchedule = () => {
    const id = `sched_${Date.now()}`
    const newSched: Schedule = {
      id,
      source_id: newSchedule.source_id,
      source_name: "New Source",
      frequency: newSchedule.frequency,
      cron_expression: newSchedule.cron_expression || undefined,
      timezone: newSchedule.timezone,
      enabled: true,
      next_run: new Date(Date.now() + 86400000).toISOString(),
      last_run: null,
      created_at: new Date().toISOString(),
    }
    setSchedules((prev) => [...prev, newSched])
    setShowAddForm(false)
    setNewSchedule({
      source_id: "",
      frequency: "daily",
      timezone: "Asia/Seoul",
      cron_expression: "",
    })
    toast.success("스케줄이 추가되었습니다!")
  }

  const stats = {
    total: schedules.length,
    active: schedules.filter((s) => s.enabled).length,
    inactive: schedules.filter((s) => !s.enabled).length,
    nextRun: schedules
      .filter((s) => s.enabled)
      .sort((a, b) => new Date(a.next_run).getTime() - new Date(b.next_run).getTime())[0]
      ?.next_run,
  }

  return (
    <div className="space-y-6 p-6">
      <Navbar title="크롤링 스케줄러" subtitle="Automated Crawling Schedule" />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="전체 스케줄" value={stats.total}  />
        <StatCard title="활성 스케줄" value={stats.active}  changeType="neutral" />
        <StatCard title="비활성 스케줄" value={stats.inactive}  changeType="neutral" />
        <StatCard
          title="다음 실행"
          value={stats.nextRun ? new Date(stats.nextRun).toLocaleString("ko-KR") : "없음"}
          
          changeType="neutral"
        />
      </div>

      {/* Add Schedule Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-stone-100">새 스케줄 추가</CardTitle>
            <CardDescription className="text-stone-400">
              자동 크롤링 스케줄을 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="source" className="text-stone-300">
                  소스 ID
                </Label>
                <Input
                  id="source"
                  placeholder="예: product_catalog"
                  value={newSchedule.source_id}
                  onChange={(e) =>
                    setNewSchedule((prev) => ({ ...prev, source_id: e.target.value }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="frequency" className="text-stone-300">
                  실행 주기
                </Label>
                <Select
                  value={newSchedule.frequency}
                  onValueChange={(value: Schedule["frequency"]) =>
                    setNewSchedule((prev) => ({ ...prev, frequency: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hourly">매시간</SelectItem>
                    <SelectItem value="daily">매일</SelectItem>
                    <SelectItem value="weekly">매주</SelectItem>
                    <SelectItem value="monthly">매월</SelectItem>
                    <SelectItem value="custom">커스텀 (Cron)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {newSchedule.frequency === "custom" && (
              <div className="space-y-2">
                <Label htmlFor="cron" className="text-stone-300">
                  Cron Expression
                </Label>
                <Input
                  id="cron"
                  placeholder="0 2 * * *"
                  value={newSchedule.cron_expression}
                  onChange={(e) =>
                    setNewSchedule((prev) => ({ ...prev, cron_expression: e.target.value }))
                  }
                />
                <p className="text-xs text-stone-500">
                  예: "0 2 * * *" = 매일 오전 2시
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="timezone" className="text-stone-300">
                Timezone
              </Label>
              <Select
                value={newSchedule.timezone}
                onValueChange={(value) =>
                  setNewSchedule((prev) => ({ ...prev, timezone: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Asia/Seoul">Asia/Seoul (KST)</SelectItem>
                  <SelectItem value="UTC">UTC</SelectItem>
                  <SelectItem value="America/New_York">America/New_York (EST)</SelectItem>
                  <SelectItem value="Europe/London">Europe/London (GMT)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleAddSchedule} className="flex-1">
                +
                스케줄 추가
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowAddForm(false)}
                className="flex-1"
              >
                취소
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schedules Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-stone-100">스케줄 목록</CardTitle>
              <CardDescription className="text-stone-400">
                자동 크롤링 스케줄 ({schedules.length}개)
              </CardDescription>
            </div>
            {!showAddForm && (
              <Button onClick={() => setShowAddForm(true)} className="gap-2">
                +
                스케줄 추가
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-stone-900 hover:bg-stone-950">
                <TableHead className="text-stone-400">소스</TableHead>
                <TableHead className="text-stone-400">주기</TableHead>
                <TableHead className="text-stone-400">Timezone</TableHead>
                <TableHead className="text-stone-400">다음 실행</TableHead>
                <TableHead className="text-stone-400">마지막 실행</TableHead>
                <TableHead className="text-stone-400">상태</TableHead>
                <TableHead className="text-stone-400">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.map((schedule) => (
                <TableRow key={schedule.id} className="border-stone-900 hover:bg-stone-950">
                  <TableCell className="text-stone-100">{schedule.source_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {schedule.frequency === "hourly" && "매시간"}
                      {schedule.frequency === "daily" && "매일"}
                      {schedule.frequency === "weekly" && "매주"}
                      {schedule.frequency === "monthly" && "매월"}
                      {schedule.frequency === "custom" && "커스텀"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-stone-400">{schedule.timezone}</TableCell>
                  <TableCell className="text-stone-100">
                    {new Date(schedule.next_run).toLocaleString("ko-KR")}
                  </TableCell>
                  <TableCell className="text-stone-400">
                    {schedule.last_run
                      ? new Date(schedule.last_run).toLocaleString("ko-KR")
                      : "없음"}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={schedule.enabled}
                        onCheckedChange={() => handleToggleSchedule(schedule.id)}
                      />
                      <Badge variant={schedule.enabled ? "success" : "secondary"}>
                        {schedule.enabled ? "활성" : "비활성"}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="sm" className="text-stone-400 hover:text-stone-300">
                          Delete
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>스케줄 삭제</AlertDialogTitle>
                          <AlertDialogDescription>
                            정말 이 스케줄을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>취소</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => handleDeleteSchedule(schedule.id)}
                            className="bg-stone-900 text-stone-100 hover:bg-stone-800"
                          >
                            삭제
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
