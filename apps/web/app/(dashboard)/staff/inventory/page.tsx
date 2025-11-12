"use client"

import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export default function InventoryPage() {
  const inventory = [
    { id: "MAT-001", name: "PET 원료", current: 1245, min: 1000, max: 2000, unit: "kg", status: "normal", location: "창고 A" },
    { id: "MAT-002", name: "PP 원료", current: 856, min: 1000, max: 2000, unit: "kg", status: "low", location: "창고 A" },
    { id: "MAT-003", name: "라벨 용지", current: 3420, min: 2000, max: 5000, unit: "롤", status: "normal", location: "창고 B" },
    { id: "PROD-001", name: "완제품 50ml", current: 4567, min: 3000, max: 6000, unit: "개", status: "normal", location: "완제품 창고" },
    { id: "PROD-002", name: "완제품 100ml", current: 2890, min: 2000, max: 5000, unit: "개", status: "normal", location: "완제품 창고" },
  ]

  return (
    <div>
      <Navbar title="재고 관리" subtitle="원자재 및 완제품 재고 현황" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">총 재고 품목</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">{inventory.length}</div>
              <p className="text-xs text-stone-500">품목</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">정상 재고</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">
                {inventory.filter(i => i.status === "normal").length}
              </div>
              <p className="text-xs text-stone-400">정상 범위</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">부족 재고</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">
                {inventory.filter(i => i.status === "low").length}
              </div>
              <p className="text-xs text-stone-400">주문 필요</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">재고 가치</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">$125K</div>
              <p className="text-xs text-stone-500">예상 금액</p>
            </CardContent>
          </Card>
        </div>

        {/* Inventory List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>재고 목록</CardTitle>
                <CardDescription>전체 재고 현황</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">입고 등록</Button>
                <Button>출고 등록</Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {inventory.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center gap-4 rounded-lg bg-stone-950 p-4 transition-colors hover:bg-stone-900"
                >
                  <div className={`h-3 w-3 rounded-full ${
                    item.status === "low" ? "bg-stone-800" :
                    item.status === "high" ? "bg-stone-700" :
                    "bg-stone-600"
                  }`} />
                  <div className="flex-1 grid grid-cols-5 gap-4">
                    <div>
                      <p className="text-xs text-stone-500">품목 코드</p>
                      <p className="text-sm font-medium text-stone-100">{item.id}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">품목명</p>
                      <p className="text-sm font-medium text-stone-100">{item.name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">현재 재고</p>
                      <p className="text-sm font-medium text-stone-100">{item.current.toLocaleString()} {item.unit}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">안전 재고</p>
                      <p className="text-sm font-medium text-stone-100">{item.min.toLocaleString()} {item.unit}</p>
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">보관 위치</p>
                      <p className="text-sm font-medium text-stone-100">{item.location}</p>
                    </div>
                  </div>
                  <Badge className={
                    item.status === "low" ? "bg-stone-800 text-stone-300" :
                    item.status === "high" ? "bg-stone-700 text-stone-300" :
                    "bg-stone-600 text-stone-100"
                  }>
                    {item.status === "low" ? "부족" : item.status === "high" ? "과다" : "정상"}
                  </Badge>
                  <Button size="sm" variant="ghost">상세</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>최근 입고 내역</CardTitle>
              <CardDescription>최근 7일간 입고</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { date: "2025-11-10", item: "PET 원료", qty: 500, unit: "kg" },
                  { date: "2025-11-09", item: "라벨 용지", qty: 1000, unit: "롤" },
                  { date: "2025-11-08", item: "PP 원료", qty: 800, unit: "kg" },
                ].map((tx, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-stone-950 p-3">
                    <div>
                      <p className="text-sm font-medium text-stone-100">{tx.item}</p>
                      <p className="text-xs text-stone-500">{tx.date}</p>
                    </div>
                    <p className="text-sm font-semibold text-stone-100">+{tx.qty.toLocaleString()} {tx.unit}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>최근 출고 내역</CardTitle>
              <CardDescription>최근 7일간 출고</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { date: "2025-11-11", item: "완제품 50ml", qty: 1200, unit: "개" },
                  { date: "2025-11-10", item: "완제품 100ml", qty: 800, unit: "개" },
                  { date: "2025-11-09", item: "완제품 50ml", qty: 950, unit: "개" },
                ].map((tx, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-stone-950 p-3">
                    <div>
                      <p className="text-sm font-medium text-stone-100">{tx.item}</p>
                      <p className="text-xs text-stone-500">{tx.date}</p>
                    </div>
                    <p className="text-sm font-semibold text-stone-100">-{tx.qty.toLocaleString()} {tx.unit}</p>
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
