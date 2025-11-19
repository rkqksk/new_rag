"use client"

import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
export default function BillingPage() {
  return (
    <div>
      <Navbar title="결제 및 청구" subtitle="구독 및 청구 정보 관리" />

      <div className="p-6 space-y-6">
        {/* Current Plan */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>현재 요금제</CardTitle>
                <CardDescription>Enterprise 플랜</CardDescription>
              </div>
              <Badge variant="default" className="bg-stone-700 text-stone-100">
                활성
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-sm text-stone-400">월 사용량</p>
                <p className="mt-1 text-2xl font-bold text-stone-100">$2,450</p>
                <p className="mt-1 text-xs text-stone-500">한도: $5,000</p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-stone-900">
                  <div className="h-full w-[49%] bg-stone-700" />
                </div>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-sm text-stone-400">API 호출</p>
                <p className="mt-1 text-2xl font-bold text-stone-100">124.5K</p>
                <p className="mt-1 text-xs text-stone-500">한도: 500K</p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-stone-900">
                  <div className="h-full w-[25%] bg-stone-700" />
                </div>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-sm text-stone-400">스토리지</p>
                <p className="mt-1 text-2xl font-bold text-stone-100">45.2GB</p>
                <p className="mt-1 text-xs text-stone-500">한도: 100GB</p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-stone-900">
                  <div className="h-full w-[45%] bg-stone-700" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Subscription Tiers */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-stone-100">요금제 선택</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                name: "Basic",
                price: "$49",
                period: "월",
                features: ["10K API 호출/월", "10GB 스토리지", "이메일 지원", "기본 분석"],
                current: false,
              },
              {
                name: "Pro",
                price: "$199",
                period: "월",
                features: ["100K API 호출/월", "50GB 스토리지", "우선 지원", "고급 분석", "웹훅"],
                current: false,
              },
              {
                name: "Enterprise",
                price: "$499",
                period: "월",
                features: ["500K API 호출/월", "100GB 스토리지", "전담 지원", "맞춤형 분석", "SLA 보장"],
                current: true,
              },
            ].map((plan) => (
              <Card
                key={plan.name}
                className={`relative ${plan.current ? "border-stone-600" : ""}`}
              >
                {plan.current && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-stone-700 text-stone-100">현재 플랜</Badge>
                  </div>
                )}
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <div className="mt-2">
                    <span className="text-3xl font-bold text-stone-100">{plan.price}</span>
                    <span className="text-stone-400">/{plan.period}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2 text-sm text-stone-300">
                        <div className="h-1.5 w-1.5 rounded-full bg-stone-600" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant={plan.current ? "outline" : "default"}
                    className="mt-4 w-full"
                    disabled={plan.current}
                  >
                    {plan.current ? "현재 플랜" : "선택하기"}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Payment Methods */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>결제 수단</CardTitle>
                <CardDescription>등록된 결제 방법</CardDescription>
              </div>
              <Button variant="outline" size="sm">
                Card
                새 카드 추가
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { type: "Visa", last4: "4242", expiry: "12/25", default: true },
                { type: "Mastercard", last4: "5555", expiry: "09/26", default: false },
              ].map((card) => (
                <div
                  key={card.last4}
                  className="flex items-center justify-between rounded-lg bg-stone-950 p-4"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-14 items-center justify-center rounded bg-stone-800">
                      Card
                    </div>
                    <div>
                      <p className="text-sm font-medium text-stone-100">
                        {card.type} •••• {card.last4}
                      </p>
                      <p className="text-xs text-stone-500">만료: {card.expiry}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {card.default && (
                      <Badge variant="outline" className="bg-stone-800 text-stone-300">
                        기본
                      </Badge>
                    )}
                    <Button variant="ghost" size="sm">
                      삭제
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Invoices */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>청구서 내역</CardTitle>
                <CardDescription>최근 청구서 및 결제 내역</CardDescription>
              </div>
              <Button variant="outline" size="sm">
                Download
                전체 다운로드
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { id: "INV-2024-11", date: "2024-11-01", amount: "$2,450", status: "paid" },
                { id: "INV-2024-10", date: "2024-10-01", amount: "$2,280", status: "paid" },
                { id: "INV-2024-09", date: "2024-09-01", amount: "$2,150", status: "paid" },
                { id: "INV-2024-08", date: "2024-08-01", amount: "$2,340", status: "paid" },
              ].map((invoice) => (
                <div
                  key={invoice.id}
                  className="flex items-center justify-between rounded-lg bg-stone-950 p-4 hover:bg-stone-900 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                      Date
                    </div>
                    <div>
                      <p className="text-sm font-medium text-stone-100">{invoice.id}</p>
                      <p className="text-xs text-stone-500">{invoice.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-semibold text-stone-100">{invoice.amount}</span>
                    <Badge variant="outline" className="bg-stone-800 text-stone-300">
                      {invoice.status === "paid" ? "지불 완료" : "대기"}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      Download
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Usage Trends */}
        <Card>
          <CardHeader>
            <CardTitle>사용량 추이</CardTitle>
            <CardDescription>최근 6개월 사용 패턴</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] flex items-end justify-around gap-2">
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
                      style={{ height: `${data.value * 2}px` }}
                    />
                  </div>
                  <span className="text-xs text-stone-400">{data.month}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-stone-400">
              ↗
              <span>평균 월 증가율: 8.5%</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
