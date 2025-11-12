import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function AdminPage() {
  return (
    <div>
      <Navbar title="관리 대시보드" subtitle="비즈니스 분석 및 운영 현황" />

      <div className="p-6 space-y-6">
        {/* Revenue Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="이번 달 수익"
            value="$12.5K"
            change="+18.2% from last month"
            changeType="increase"
            
          />
          <StatCard
            title="신규 고객"
            value="34"
            change="+12 from last month"
            changeType="increase"
            
          />
          <StatCard
            title="총 주문"
            value="156"
            change="+23.1% from last month"
            changeType="increase"
            
          />
          <StatCard
            title="처리율"
            value="94.2%"
            change="+2.3% from last month"
            changeType="increase"
            
          />
        </div>

        {/* Charts Row */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>월별 매출 추이</CardTitle>
              <CardDescription>최근 6개월 매출 데이터</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-end justify-around gap-2">
                {[
                  { month: "6월", value: 65 },
                  { month: "7월", value: 72 },
                  { month: "8월", value: 68 },
                  { month: "9월", value: 85 },
                  { month: "10월", value: 90 },
                  { month: "11월", value: 95 },
                ].map((data) => (
                  <div key={data.month} className="flex flex-col items-center gap-2 flex-1">
                    <div className="relative w-full">
                      <div
                        className="w-full bg-stone-700 rounded-t-lg transition-all duration-500 hover:bg-stone-600"
                        style={{ height: `${data.value * 3}px` }}
                      />
                    </div>
                    <span className="text-xs text-stone-400">{data.month}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>고객 분포</CardTitle>
              <CardDescription>고객 유형별 현황</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { type: "Enterprise", count: 12, percentage: 35, color: "bg-stone-700" },
                  { type: "VIP", count: 28, percentage: 28, color: "bg-stone-600" },
                  { type: "Regular", count: 89, percentage: 37, color: "bg-stone-600" },
                ].map((customer) => (
                  <div key={customer.type} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`h-3 w-3 rounded-full ${customer.color}`} />
                        <span className="text-sm text-stone-300">{customer.type}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-medium text-stone-100">{customer.count}</span>
                        <span className="text-xs text-stone-500 w-12 text-right">{customer.percentage}%</span>
                      </div>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className={`h-full ${customer.color} transition-all duration-500`}
                        style={{ width: `${customer.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Orders */}
        <Card>
          <CardHeader>
            <CardTitle>최근 주문</CardTitle>
            <CardDescription>최근 처리된 주문 내역</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { id: "ORD-2401", customer: "ABC Corp", amount: "$2,450", status: "completed", date: "2025-11-08" },
                { id: "ORD-2402", customer: "XYZ Ltd", amount: "$1,890", status: "processing", date: "2025-11-08" },
                { id: "ORD-2403", customer: "Tech Solutions", amount: "$3,200", status: "completed", date: "2025-11-07" },
                { id: "ORD-2404", customer: "Design Studio", amount: "$890", status: "pending", date: "2025-11-07" },
                { id: "ORD-2405", customer: "Marketing Inc", amount: "$1,250", status: "completed", date: "2025-11-07" },
              ].map((order) => (
                <div key={order.id} className="flex items-center gap-4 rounded-lg bg-stone-950 p-3 hover:bg-stone-900 transition-colors">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800 font-mono text-xs text-stone-400">
                    {order.id.split('-')[1]}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-stone-100">{order.customer}</p>
                    <p className="text-xs text-stone-500">{order.id}</p>
                  </div>
                  <span className="text-sm font-semibold text-stone-100">{order.amount}</span>
                  <Badge variant={
                    order.status === "completed" ? "success" :
                    order.status === "processing" ? "warning" :
                    "secondary"
                  }>
                    {order.status}
                  </Badge>
                  <span className="text-xs text-stone-500 w-20 text-right">{order.date}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* API Usage */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>API 키 현황</CardTitle>
              <CardDescription>활성 API 키 및 사용량</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: "Production API", key: "pk_live_***", calls: "12.4K", limit: "50K" },
                  { name: "Development API", key: "pk_dev_***", calls: "3.2K", limit: "10K" },
                  { name: "Test API", key: "pk_test_***", calls: "892", limit: "5K" },
                ].map((api) => (
                  <div key={api.key} className="rounded-lg bg-stone-950 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-stone-100">{api.name}</p>
                        <p className="font-mono text-xs text-stone-500">{api.key}</p>
                      </div>
                      <Badge variant="outline">{api.calls} / {api.limit}</Badge>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className="h-full bg-stone-600 transition-all duration-500"
                        style={{ width: `${(parseInt(api.calls.replace('K', '000')) / parseInt(api.limit.replace('K', '000'))) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>결제 통계</CardTitle>
              <CardDescription>이번 달 결제 현황</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="rounded-lg bg-stone-950 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm text-stone-400">성공</span>
                    <span className="text-lg font-bold text-stone-300">142</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                    <div className="h-full w-[91%] bg-stone-700" />
                  </div>
                </div>
                <div className="rounded-lg bg-stone-950 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-sm text-stone-400">실패</span>
                    <span className="text-lg font-bold text-stone-400">14</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                    <div className="h-full w-[9%] bg-stone-800" />
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between rounded-lg bg-stone-800 p-3">
                  <span className="text-sm text-stone-300">성공률</span>
                  <span className="text-xl font-bold text-stone-100">91.0%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
