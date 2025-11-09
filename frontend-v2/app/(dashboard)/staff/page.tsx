import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function StaffPage() {
  return (
    <div>
      <Navbar title="제조 관리" subtitle="생산 현황 및 품질 관리" />

      <div className="p-6 space-y-6">
        {/* Production Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="금일 생산량"
            value="1,245"
            change="+5.2% from yesterday"
            changeType="increase"
            icon="🏭"
          />
          <StatCard
            title="불량률"
            value="2.1%"
            change="-0.3% from yesterday"
            changeType="increase"
            icon="✅"
          />
          <StatCard
            title="재고량"
            value="4,567"
            change="정상 범위"
            changeType="neutral"
            icon="📦"
          />
          <StatCard
            title="가동률"
            value="87.3%"
            change="+2.1% from yesterday"
            changeType="increase"
            icon="⚙️"
          />
        </div>

        {/* Production Line Status */}
        <Card>
          <CardHeader>
            <CardTitle>생산 라인 현황</CardTitle>
            <CardDescription>실시간 생산 라인 모니터링</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                { line: "라인 A", status: "운영중", output: "425", target: "500", efficiency: 85 },
                { line: "라인 B", status: "운영중", output: "462", target: "500", efficiency: 92 },
                { line: "라인 C", status: "점검중", output: "0", target: "500", efficiency: 0 },
              ].map((line) => (
                <div key={line.line} className="rounded-lg border border-stone-800 bg-stone-950 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="font-semibold text-stone-100">{line.line}</h3>
                    <Badge variant={line.status === "운영중" ? "success" : "warning"}>
                      {line.status}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-stone-400">생산량</span>
                      <span className="text-stone-100">{line.output} / {line.target}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className={`h-full transition-all duration-500 ${
                          line.efficiency >= 80 ? "bg-green-600" :
                          line.efficiency >= 60 ? "bg-yellow-600" :
                          "bg-red-600"
                        }`}
                        style={{ width: `${line.efficiency}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-stone-400">효율</span>
                      <span className="text-stone-100">{line.efficiency}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quality Control */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>품질 검사 결과</CardTitle>
              <CardDescription>최근 24시간 검사 현황</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { type: "외관 검사", passed: 456, failed: 12, total: 468 },
                  { type: "치수 검사", passed: 445, failed: 8, total: 453 },
                  { type: "기능 검사", passed: 438, failed: 15, total: 453 },
                  { type: "강도 검사", passed: 441, failed: 6, total: 447 },
                ].map((test) => (
                  <div key={test.type} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-stone-300">{test.type}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-green-400">{test.passed}</span>
                        <span className="text-sm text-red-400">{test.failed}</span>
                        <span className="text-xs text-stone-500">/ {test.total}</span>
                      </div>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                      <div className="flex h-full">
                        <div
                          className="bg-green-600"
                          style={{ width: `${(test.passed / test.total) * 100}%` }}
                        />
                        <div
                          className="bg-red-600"
                          style={{ width: `${(test.failed / test.total) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>불량 유형 분석</CardTitle>
              <CardDescription>주요 불량 원인</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { type: "표면 결함", count: 18, percentage: 43 },
                  { type: "치수 불량", count: 12, percentage: 29 },
                  { type: "색상 편차", count: 8, percentage: 19 },
                  { type: "기타", count: 4, percentage: 9 },
                ].map((defect) => (
                  <div key={defect.type} className="flex items-center gap-3 rounded-lg bg-stone-950 p-3">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-stone-100">{defect.type}</p>
                      <div className="mt-1 h-2 overflow-hidden rounded-full bg-stone-900">
                        <div
                          className="h-full bg-red-600 transition-all duration-500"
                          style={{ width: `${defect.percentage}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-stone-100">{defect.count}</p>
                      <p className="text-xs text-stone-500">{defect.percentage}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Inventory Status */}
        <Card>
          <CardHeader>
            <CardTitle>재고 현황</CardTitle>
            <CardDescription>원자재 및 완제품 재고</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { item: "PET 원료", current: 1245, min: 1000, max: 2000, unit: "kg", status: "normal" },
                { item: "PP 원료", current: 856, min: 1000, max: 2000, unit: "kg", status: "low" },
                { item: "라벨 용지", current: 3420, min: 2000, max: 5000, unit: "롤", status: "normal" },
                { item: "완제품 (50ml)", current: 4567, min: 3000, max: 6000, unit: "개", status: "normal" },
                { item: "완제품 (100ml)", current: 2890, min: 2000, max: 5000, unit: "개", status: "normal" },
              ].map((item) => (
                <div key={item.item} className="flex items-center gap-4 rounded-lg bg-stone-950 p-3 hover:bg-stone-900 transition-colors">
                  <div className={`h-2 w-2 rounded-full ${
                    item.status === "low" ? "bg-red-500" :
                    item.status === "high" ? "bg-yellow-500" :
                    "bg-green-500"
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-stone-100">{item.item}</p>
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className={`h-full transition-all duration-500 ${
                          item.current < item.min ? "bg-red-600" :
                          item.current > item.max ? "bg-yellow-600" :
                          "bg-green-600"
                        }`}
                        style={{ width: `${(item.current / item.max) * 100}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-stone-100">{item.current.toLocaleString()}</p>
                    <p className="text-xs text-stone-500">{item.unit}</p>
                  </div>
                  <Badge variant={
                    item.status === "low" ? "destructive" :
                    item.status === "high" ? "warning" :
                    "success"
                  }>
                    {item.status === "low" ? "부족" : item.status === "high" ? "과다" : "정상"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
