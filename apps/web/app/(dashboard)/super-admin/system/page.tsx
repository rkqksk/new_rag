"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"

export default function SystemPage() {
  const [settings, setSettings] = useState({
    maintenanceMode: false,
    newUserSignup: true,
    emailNotifications: true,
    apiRateLimit: "1000",
    sessionTimeout: "30",
    debugMode: false,
  })

  const services = [
    { name: "API Server", status: "running", uptime: "15d 4h 23m", cpu: "12%", memory: "2.4GB" },
    { name: "Database (PostgreSQL)", status: "running", uptime: "15d 4h 23m", cpu: "8%", memory: "1.8GB" },
    { name: "Redis Cache", status: "running", uptime: "15d 4h 23m", cpu: "3%", memory: "512MB" },
    { name: "Qdrant Vector DB", status: "running", uptime: "15d 4h 23m", cpu: "5%", memory: "1.2GB" },
    { name: "Celery Worker", status: "running", uptime: "15d 4h 23m", cpu: "15%", memory: "800MB" },
  ]

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div>
      <Navbar title="시스템 설정" subtitle="전체 시스템 구성 및 서비스 관리" />

      <div className="p-6 space-y-6">
        {/* Service Status */}
        <Card>
          <CardHeader>
            <CardTitle>서비스 상태</CardTitle>
            <CardDescription>시스템 구성 요소 및 상태 모니터링</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {services.map((service) => (
                <div
                  key={service.name}
                  className="flex items-center gap-4 rounded-lg bg-stone-950 p-4"
                >
                  <Badge variant="default" className="bg-green-900 text-green-100">
                    {service.status}
                  </Badge>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-stone-100">{service.name}</p>
                    <p className="text-xs text-stone-500">Uptime: {service.uptime}</p>
                  </div>
                  <div className="flex gap-6 text-sm">
                    <div>
                      <span className="text-stone-500">CPU: </span>
                      <span className="text-stone-100">{service.cpu}</span>
                    </div>
                    <div>
                      <span className="text-stone-500">Memory: </span>
                      <span className="text-stone-100">{service.memory}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost">재시작</Button>
                    <Button size="sm" variant="ghost">로그</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Settings */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>일반 설정</CardTitle>
              <CardDescription>시스템 운영 설정</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>유지보수 모드</Label>
                  <p className="text-xs text-stone-500">시스템 점검 중 사용자 접근 제한</p>
                </div>
                <Switch
                  checked={settings.maintenanceMode}
                  onCheckedChange={(checked) => handleSettingChange("maintenanceMode", checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>신규 회원가입</Label>
                  <p className="text-xs text-stone-500">새로운 사용자 등록 허용</p>
                </div>
                <Switch
                  checked={settings.newUserSignup}
                  onCheckedChange={(checked) => handleSettingChange("newUserSignup", checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>이메일 알림</Label>
                  <p className="text-xs text-stone-500">시스템 이벤트 이메일 알림</p>
                </div>
                <Switch
                  checked={settings.emailNotifications}
                  onCheckedChange={(checked) => handleSettingChange("emailNotifications", checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>디버그 모드</Label>
                  <p className="text-xs text-stone-500">상세 로그 및 오류 정보 출력</p>
                </div>
                <Switch
                  checked={settings.debugMode}
                  onCheckedChange={(checked) => handleSettingChange("debugMode", checked)}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>성능 설정</CardTitle>
              <CardDescription>API 및 세션 제한</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="apiRateLimit">API Rate Limit (요청/분)</Label>
                <Input
                  id="apiRateLimit"
                  type="number"
                  value={settings.apiRateLimit}
                  onChange={(e) => handleSettingChange("apiRateLimit", e.target.value)}
                />
                <p className="text-xs text-stone-500">사용자당 분당 최대 API 요청 수</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sessionTimeout">세션 타임아웃 (분)</Label>
                <Input
                  id="sessionTimeout"
                  type="number"
                  value={settings.sessionTimeout}
                  onChange={(e) => handleSettingChange("sessionTimeout", e.target.value)}
                />
                <p className="text-xs text-stone-500">비활성 세션 만료 시간</p>
              </div>

              <Button className="w-full">설정 저장</Button>
            </CardContent>
          </Card>
        </div>

        {/* System Information */}
        <Card>
          <CardHeader>
            <CardTitle>시스템 정보</CardTitle>
            <CardDescription>서버 및 소프트웨어 버전</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-500">Operating System</p>
                <p className="text-sm font-medium text-stone-100">Ubuntu 22.04 LTS</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-500">Python Version</p>
                <p className="text-sm font-medium text-stone-100">3.11.5</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-500">FastAPI Version</p>
                <p className="text-sm font-medium text-stone-100">0.109.0</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-500">PostgreSQL Version</p>
                <p className="text-sm font-medium text-stone-100">15.3</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-500">Redis Version</p>
                <p className="text-sm font-medium text-stone-100">7.2.3</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-500">Qdrant Version</p>
                <p className="text-sm font-medium text-stone-100">1.7.4</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
