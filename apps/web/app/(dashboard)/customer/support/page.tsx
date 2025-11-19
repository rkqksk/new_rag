"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
interface Ticket {
  id: string
  subject: string
  category: string
  status: "open" | "in-progress" | "resolved" | "closed"
  priority: "low" | "medium" | "high" | "urgent"
  created: string
  updated: string
  messages: number
  assignee?: string
}

export default function SupportPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [showNewTicket, setShowNewTicket] = useState(false)

  const tickets: Ticket[] = [
    {
      id: "TKT-1234",
      subject: "50ml PET 병 견적 문의",
      category: "견적 문의",
      status: "in-progress",
      priority: "medium",
      created: "2025-11-08 14:23",
      updated: "2025-11-11 09:15",
      messages: 3,
      assignee: "김지원",
    },
    {
      id: "TKT-1233",
      subject: "배송지 변경 요청",
      category: "배송 문의",
      status: "resolved",
      priority: "high",
      created: "2025-11-07 16:45",
      updated: "2025-11-09 11:30",
      messages: 5,
      assignee: "이민수",
    },
    {
      id: "TKT-1232",
      subject: "제품 샘플 요청",
      category: "제품 문의",
      status: "open",
      priority: "low",
      created: "2025-11-06 10:20",
      updated: "2025-11-06 10:20",
      messages: 1,
    },
    {
      id: "TKT-1231",
      subject: "대량 주문 할인 문의",
      category: "견적 문의",
      status: "in-progress",
      priority: "high",
      created: "2025-11-05 13:15",
      updated: "2025-11-10 15:45",
      messages: 8,
      assignee: "박서연",
    },
    {
      id: "TKT-1230",
      subject: "결제 오류 문제",
      category: "기술 지원",
      status: "closed",
      priority: "urgent",
      created: "2025-11-03 09:30",
      updated: "2025-11-04 14:20",
      messages: 6,
      assignee: "최준호",
    },
  ]

  const statusConfig = {
    open: {
      label: "대기중",
      icon: Clock,
      color: "bg-stone-800 text-stone-300",
    },
    "in-progress": {
      label: "처리중",
      icon: MessageSquare,
      color: "bg-stone-700 text-stone-100",
    },
    resolved: {
      label: "해결됨",
      icon: CheckCircle,
      color: "bg-stone-600 text-stone-100",
    },
    closed: {
      label: "종료됨",
      icon: XCircle,
      color: "bg-stone-900 text-stone-400",
    },
  }

  const priorityConfig = {
    low: { label: "낮음", color: "bg-stone-800 text-stone-300" },
    medium: { label: "보통", color: "bg-stone-700 text-stone-200" },
    high: { label: "높음", color: "bg-stone-700 text-stone-100" },
    urgent: { label: "긴급", color: "bg-stone-600 text-stone-100" },
  }

  const categories = ["all", "견적 문의", "배송 문의", "제품 문의", "기술 지원", "기타"]

  const filteredTickets = tickets.filter(
    (ticket) => selectedCategory === "all" || ticket.category === selectedCategory
  )

  return (
    <div>
      <Navbar title="고객 지원" subtitle="문의사항 및 티켓 관리" />

      <div className="p-6 space-y-6">
        {/* Support Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  <MessageSquare className="h-5 w-5 text-stone-400" />
                </div>
                <div>
                  <p className="text-xs text-stone-400">전체 티켓</p>
                  <p className="text-2xl font-bold text-stone-100">{tickets.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  Time
                </div>
                <div>
                  <p className="text-xs text-stone-400">대기중</p>
                  <p className="text-2xl font-bold text-stone-100">
                    {tickets.filter((t) => t.status === "open").length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  ⚠
                </div>
                <div>
                  <p className="text-xs text-stone-400">처리중</p>
                  <p className="text-2xl font-bold text-stone-100">
                    {tickets.filter((t) => t.status === "in-progress").length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div>
                <p className="text-xs text-stone-400">평균 응답 시간</p>
                <p className="text-2xl font-bold text-stone-100">2.4시간</p>
                <p className="text-xs text-stone-500 mt-1">지난 30일</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* New Ticket Button */}
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            {categories.map((category) => (
              <Badge
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                className={`cursor-pointer ${
                  selectedCategory === category
                    ? "bg-stone-700 text-stone-100"
                    : "hover:bg-stone-800"
                }`}
                onClick={() => setSelectedCategory(category)}
              >
                {category === "all" ? "전체" : category}
              </Badge>
            ))}
          </div>
          <Button onClick={() => setShowNewTicket(!showNewTicket)}>
            +
            새 티켓
          </Button>
        </div>

        {/* New Ticket Form */}
        {showNewTicket && (
          <Card className="border-stone-700">
            <CardHeader>
              <CardTitle>새 지원 티켓 생성</CardTitle>
              <CardDescription>문의사항을 자세히 작성해주세요</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-stone-300">제목</label>
                  <Input placeholder="문의 제목을 입력하세요" className="mt-1" />
                </div>
                <div>
                  <label className="text-sm font-medium text-stone-300">카테고리</label>
                  <select className="mt-1 w-full rounded-md border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-stone-100">
                    <option>견적 문의</option>
                    <option>배송 문의</option>
                    <option>제품 문의</option>
                    <option>기술 지원</option>
                    <option>기타</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-stone-300">우선순위</label>
                  <select className="mt-1 w-full rounded-md border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-stone-100">
                    <option>낮음</option>
                    <option>보통</option>
                    <option>높음</option>
                    <option>긴급</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-stone-300">내용</label>
                  <Textarea
                    placeholder="문의 내용을 상세히 작성해주세요"
                    className="mt-1 min-h-32"
                  />
                </div>
                <div className="flex justify-between">
                  <Button variant="outline">
                    <Paperclip className="mr-2 h-4 w-4" />
                    파일 첨부
                  </Button>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setShowNewTicket(false)}>
                      취소
                    </Button>
                    <Button>
                      Send
                      제출
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tickets List */}
        <div className="space-y-4">
          {filteredTickets.map((ticket) => {
            const StatusIcon = statusConfig[ticket.status].icon
            return (
              <Card key={ticket.id} className="cursor-pointer hover:border-stone-600 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-2">
                        <h3 className="text-base font-semibold text-stone-100">{ticket.subject}</h3>
                        <Badge variant="outline" className="bg-stone-900 text-stone-400 text-xs">
                          {ticket.id}
                        </Badge>
                      </div>

                      <div className="mb-3 flex flex-wrap gap-2">
                        <Badge variant="outline" className="bg-stone-900 text-stone-400 text-xs">
                          {ticket.category}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`${statusConfig[ticket.status].color} text-xs`}
                        >
                          <StatusIcon className="mr-1 h-3 w-3" />
                          {statusConfig[ticket.status].label}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`${priorityConfig[ticket.priority].color} text-xs`}
                        >
                          {priorityConfig[ticket.priority].label}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-stone-500">
                        <div>
                          <span className="text-stone-400">생성:</span> {ticket.created}
                        </div>
                        <div>
                          <span className="text-stone-400">업데이트:</span> {ticket.updated}
                        </div>
                        {ticket.assignee && (
                          <div>
                            <span className="text-stone-400">담당자:</span> {ticket.assignee}
                          </div>
                        )}
                        <div>
                          <span className="text-stone-400">메시지:</span> {ticket.messages}개
                        </div>
                      </div>
                    </div>

                    <Button variant="outline" size="sm">
                      <MessageSquare className="mr-2 h-4 w-4" />
                      답변
                    </Button>
                  </div>

                  {/* Progress Bar for In-Progress Tickets */}
                  {ticket.status === "in-progress" && (
                    <div className="mt-3 pt-3 border-t border-stone-800">
                      <div className="flex items-center justify-between text-xs text-stone-400 mb-1">
                        <span>처리 진행률</span>
                        <span>60%</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-stone-900">
                        <div className="h-full w-[60%] bg-stone-700" />
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Empty State */}
        {filteredTickets.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <MessageSquare className="mx-auto h-12 w-12 text-stone-700" />
              <p className="mt-4 text-stone-400">해당 카테고리의 티켓이 없습니다</p>
            </CardContent>
          </Card>
        )}

        {/* FAQ */}
        <Card>
          <CardHeader>
            <CardTitle>자주 묻는 질문 (FAQ)</CardTitle>
            <CardDescription>빠른 답변을 위한 가이드</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                {
                  question: "제품 견적은 어떻게 받나요?",
                  answer: "견적 문의 카테고리로 티켓을 생성하시면 됩니다.",
                },
                {
                  question: "배송은 얼마나 걸리나요?",
                  answer: "일반적으로 주문 후 3-5 영업일 소요됩니다.",
                },
                {
                  question: "최소 주문 수량이 있나요?",
                  answer: "제품별로 상이하며, 제품 페이지에서 확인 가능합니다.",
                },
                {
                  question: "샘플 요청이 가능한가요?",
                  answer: "네, 제품 문의로 샘플 요청 티켓을 생성해주세요.",
                },
              ].map((faq, idx) => (
                <div key={idx} className="rounded-lg bg-stone-950 p-4">
                  <p className="text-sm font-medium text-stone-100 mb-1">{faq.question}</p>
                  <p className="text-xs text-stone-400">{faq.answer}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Contact Info */}
        <Card>
          <CardHeader>
            <CardTitle>직접 문의</CardTitle>
            <CardDescription>긴급한 경우 직접 연락주세요</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-400 mb-1">이메일</p>
                <p className="text-sm text-stone-100">support@example.com</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-400 mb-1">전화</p>
                <p className="text-sm text-stone-100">1588-1234</p>
              </div>
              <div className="rounded-lg bg-stone-950 p-4">
                <p className="text-xs text-stone-400 mb-1">운영시간</p>
                <p className="text-sm text-stone-100">평일 09:00 - 18:00</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
