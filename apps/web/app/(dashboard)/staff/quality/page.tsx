"use client"

import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export default function QualityPage() {
  const inspections = [
    { id: "QC-001", product: "PET 용기 50ml", batch: "B20251111-001", inspector: "김철수", result: "통과", defects: 0, timestamp: "2025-11-11 09:00" },
    { id: "QC-002", product: "PET 용기 100ml", batch: "B20251111-002", inspector: "이영희", result: "통과", defects: 0, timestamp: "2025-11-11 09:15" },
    { id: "QC-003", product: "PP 용기 50ml", batch: "B20251111-003", inspector: "박민수", result: "불합격", defects: 3, timestamp: "2025-11-11 09:30" },
    { id: "QC-004", product: "PET 용기 50ml", batch: "B20251111-004", inspector: "최지영", result: "통과", defects: 0, timestamp: "2025-11-11 09:45" },
  ]

  return (
    <div>
      <Navbar title="품질 관리" subtitle="품질 검사 및 불량 분석" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">금일 검사</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">156</div>
              <p className="text-xs text-stone-500">건</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">합격률</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">97.8%</div>
              <p className="text-xs text-stone-400">+1.2% from yesterday</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">불량 건수</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">3</div>
              <p className="text-xs text-stone-400">-2 from yesterday</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">진행 중</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">8</div>
              <p className="text-xs text-stone-500">검사 대기</p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Inspections */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>최근 검사 기록</CardTitle>
                <CardDescription>오늘 진행된 품질 검사 결과</CardDescription>
              </div>
              <Button>새 검사 시작</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {inspections.map((inspection) => (
                <div
                  key={inspection.id}
                  className="flex items-center gap-4 rounded-lg bg-stone-950 p-4 transition-colors hover:bg-stone-900"
                >
                  <div className="flex-shrink-0">
                    <Badge className={
                      inspection.result === "통과"
                        ? "bg-stone-700 text-stone-100"
                        : "bg-stone-800 text-stone-300"
                    }>
                      {inspection.result}
                    </Badge>
                  </div>
                  <div className="flex-1 grid grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-stone-500">검사 ID</p>
                      <p className="text-sm font-medium text-stone-100">{inspection.id}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">제품</p>
                      <p className="text-sm font-medium text-stone-100">{inspection.product}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">검사자</p>
                      <p className="text-sm font-medium text-stone-100">{inspection.inspector}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">불량 수</p>
                      <p className="text-sm font-medium text-stone-100">{inspection.defects}개</p>
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-xs text-stone-500">
                    {inspection.timestamp}
                  </div>
                  <Button size="sm" variant="ghost">상세</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quality Metrics */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>검사 항목별 통과율</CardTitle>
              <CardDescription>주요 검사 항목 분석</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { item: "외관 검사", rate: 98.5 },
                  { item: "치수 검사", rate: 97.2 },
                  { item: "강도 검사", rate: 99.1 },
                  { item: "밀폐성 검사", rate: 96.8 },
                ].map((metric) => (
                  <div key={metric.item}>
                    <div className="mb-2 flex items-center justify-between text-sm">
                      <span className="text-stone-400">{metric.item}</span>
                      <span className="text-stone-100">{metric.rate}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                      <div
                        className="h-full bg-stone-600 transition-all duration-500"
                        style={{ width: `${metric.rate}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>검사자별 현황</CardTitle>
              <CardDescription>검사 인원별 통계</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: "김철수", inspected: 45, passed: 44, rate: 97.8 },
                  { name: "이영희", inspected: 38, passed: 37, rate: 97.4 },
                  { name: "박민수", inspected: 42, passed: 40, rate: 95.2 },
                  { name: "최지영", inspected: 31, passed: 31, rate: 100 },
                ].map((inspector) => (
                  <div key={inspector.name} className="flex items-center gap-4 rounded-lg bg-stone-950 p-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-stone-800 text-sm font-semibold text-stone-100">
                      {inspector.name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-stone-100">{inspector.name}</p>
                      <p className="text-xs text-stone-500">검사: {inspector.inspected}건 / 합격: {inspector.passed}건</p>
                    </div>
                    <div className="text-sm font-semibold text-stone-100">{inspector.rate}%</div>
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
