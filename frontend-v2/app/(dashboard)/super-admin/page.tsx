import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function SuperAdminPage() {
  return (
    <div>
      <Navbar title="시스템 개요" subtitle="전체 시스템 현황 및 모니터링" />

      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="총 사용자"
            value="1,234"
            change="+12.5% from last month"
            changeType="increase"
            icon="👥"
          />
          <StatCard
            title="API 호출"
            value="45.2K"
            change="+8.2% from last month"
            changeType="increase"
            icon="📡"
          />
          <StatCard
            title="활성 세션"
            value="89"
            change="-3 from yesterday"
            changeType="decrease"
            icon="🔌"
          />
          <StatCard
            title="시스템 상태"
            value="정상"
            subtitle="모든 서비스 운영 중"
            icon="✅"
          />
        </div>

        {/* Recent Activity */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>최근 활동</CardTitle>
              <CardDescription>최근 24시간 동안의 시스템 활동</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { user: "admin@example.com", action: "사용자 생성", time: "5분 전", type: "success" },
                  { user: "staff@example.com", action: "데이터 업로드", time: "12분 전", type: "info" },
                  { user: "system", action: "자동 백업 완료", time: "1시간 전", type: "success" },
                  { user: "customer@example.com", action: "로그인 실패", time: "2시간 전", type: "warning" },
                ].map((activity, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-lg bg-stone-950 p-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-stone-100">{activity.action}</p>
                      <p className="text-xs text-stone-500">{activity.user}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={activity.type === "success" ? "success" : activity.type === "warning" ? "warning" : "secondary"}>
                        {activity.type}
                      </Badge>
                      <span className="text-xs text-stone-500">{activity.time}</span>
                    </div>
                  </div>
                ))}
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
                  { label: "CPU", value: 45, color: "bg-blue-600" },
                  { label: "메모리", value: 68, color: "bg-green-600" },
                  { label: "디스크", value: 32, color: "bg-yellow-600" },
                  { label: "네트워크", value: 23, color: "bg-purple-600" },
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
