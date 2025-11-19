"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
interface Order {
  id: string
  date: string
  status: "pending" | "processing" | "shipped" | "delivered" | "cancelled"
  items: {
    name: string
    quantity: number
    price: string
  }[]
  total: string
  trackingNumber?: string
  estimatedDelivery?: string
}

export default function OrdersPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>("all")

  const orders: Order[] = [
    {
      id: "ORD-2024-1156",
      date: "2025-11-08",
      status: "delivered",
      items: [
        { name: "50ml PET 병 x 1000", quantity: 1000, price: "₩1,200,000" },
        { name: "펌프 헤드 x 1000", quantity: 1000, price: "₩500,000" },
      ],
      total: "₩1,700,000",
      trackingNumber: "CJ-1234567890",
      estimatedDelivery: "2025-11-10",
    },
    {
      id: "ORD-2024-1155",
      date: "2025-11-05",
      status: "shipped",
      items: [
        { name: "100ml 펌프 용기 x 500", quantity: 500, price: "₩1,250,000" },
      ],
      total: "₩1,250,000",
      trackingNumber: "CJ-9876543210",
      estimatedDelivery: "2025-11-12",
    },
    {
      id: "ORD-2024-1154",
      date: "2025-11-03",
      status: "processing",
      items: [
        { name: "30ml 스포이드 병 x 2000", quantity: 2000, price: "₩3,600,000" },
      ],
      total: "₩3,600,000",
      estimatedDelivery: "2025-11-15",
    },
    {
      id: "ORD-2024-1153",
      date: "2025-11-01",
      status: "pending",
      items: [
        { name: "250ml 샴푸 용기 x 300", quantity: 300, price: "₩960,000" },
        { name: "디스펜서 캡 x 300", quantity: 300, price: "₩180,000" },
      ],
      total: "₩1,140,000",
      estimatedDelivery: "2025-11-18",
    },
    {
      id: "ORD-2024-1152",
      date: "2025-10-28",
      status: "delivered",
      items: [
        { name: "15ml 에센스 병 x 1500", quantity: 1500, price: "₩2,250,000" },
      ],
      total: "₩2,250,000",
      trackingNumber: "CJ-5555666677",
      estimatedDelivery: "2025-11-01",
    },
    {
      id: "ORD-2024-1151",
      date: "2025-10-25",
      status: "cancelled",
      items: [
        { name: "500ml 샤워젤 용기 x 200", quantity: 200, price: "₩900,000" },
      ],
      total: "₩900,000",
    },
  ]

  const statusConfig = {
    pending: {
      label: "대기중",
      icon: Clock,
      color: "bg-stone-800 text-stone-300",
    },
    processing: {
      label: "처리중",
      icon: Package,
      color: "bg-stone-700 text-stone-100",
    },
    shipped: {
      label: "배송중",
      icon: Truck,
      color: "bg-stone-700 text-stone-100",
    },
    delivered: {
      label: "배송완료",
      icon: CheckCircle,
      color: "bg-stone-600 text-stone-100",
    },
    cancelled: {
      label: "취소됨",
      icon: XCircle,
      color: "bg-stone-900 text-stone-400",
    },
  }

  const filteredOrders = orders.filter(
    (order) => selectedStatus === "all" || order.status === selectedStatus
  )

  const getStatusBadge = (status: Order["status"]) => {
    const config = statusConfig[status]
    const Icon = config.icon
    return (
      <Badge variant="outline" className={config.color}>
        <Icon className="mr-1 h-3 w-3" />
        {config.label}
      </Badge>
    )
  }

  return (
    <div>
      <Navbar title="주문 내역" subtitle="나의 주문 현황 및 배송 추적" />

      <div className="p-6 space-y-6">
        {/* Order Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  <Package className="h-5 w-5 text-stone-400" />
                </div>
                <div>
                  <p className="text-xs text-stone-400">전체 주문</p>
                  <p className="text-2xl font-bold text-stone-100">{orders.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  <Truck className="h-5 w-5 text-stone-400" />
                </div>
                <div>
                  <p className="text-xs text-stone-400">배송중</p>
                  <p className="text-2xl font-bold text-stone-100">
                    {orders.filter((o) => o.status === "shipped").length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-stone-800">
                  ✓
                </div>
                <div>
                  <p className="text-xs text-stone-400">배송완료</p>
                  <p className="text-2xl font-bold text-stone-100">
                    {orders.filter((o) => o.status === "delivered").length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div>
                <p className="text-xs text-stone-400">총 주문 금액</p>
                <p className="text-2xl font-bold text-stone-100">₩10.9M</p>
                <p className="text-xs text-stone-500 mt-1">이번 달</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Status Filter */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2">
              <Badge
                variant={selectedStatus === "all" ? "default" : "outline"}
                className={`cursor-pointer ${
                  selectedStatus === "all" ? "bg-stone-700 text-stone-100" : "hover:bg-stone-800"
                }`}
                onClick={() => setSelectedStatus("all")}
              >
                전체
              </Badge>
              {Object.entries(statusConfig).map(([status, config]) => (
                <Badge
                  key={status}
                  variant={selectedStatus === status ? "default" : "outline"}
                  className={`cursor-pointer ${
                    selectedStatus === status
                      ? "bg-stone-700 text-stone-100"
                      : "hover:bg-stone-800"
                  }`}
                  onClick={() => setSelectedStatus(status)}
                >
                  {config.label}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Orders List */}
        <div className="space-y-4">
          {filteredOrders.map((order) => (
            <Card key={order.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">{order.id}</CardTitle>
                    <CardDescription>주문일: {order.date}</CardDescription>
                  </div>
                  {getStatusBadge(order.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Order Items */}
                  <div className="space-y-2">
                    {order.items.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-lg bg-stone-950 p-3"
                      >
                        <div className="flex-1">
                          <p className="text-sm font-medium text-stone-100">{item.name}</p>
                          <p className="text-xs text-stone-500">수량: {item.quantity}개</p>
                        </div>
                        <span className="text-sm font-semibold text-stone-100">{item.price}</span>
                      </div>
                    ))}
                  </div>

                  {/* Delivery Info */}
                  {(order.status === "shipped" || order.status === "delivered") &&
                    order.trackingNumber && (
                      <div className="rounded-lg bg-stone-950 p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-stone-400">운송장 번호</span>
                          <code className="text-xs text-stone-300">{order.trackingNumber}</code>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-stone-400">예상 도착</span>
                          <span className="text-xs text-stone-300">{order.estimatedDelivery}</span>
                        </div>
                      </div>
                    )}

                  {/* Order Status Progress */}
                  {order.status !== "cancelled" && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs text-stone-400">
                        <span>주문 진행률</span>
                        <span>
                          {order.status === "pending"
                            ? "25%"
                            : order.status === "processing"
                            ? "50%"
                            : order.status === "shipped"
                            ? "75%"
                            : "100%"}
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-stone-900">
                        <div
                          className="h-full bg-stone-700 transition-all duration-500"
                          style={{
                            width:
                              order.status === "pending"
                                ? "25%"
                                : order.status === "processing"
                                ? "50%"
                                : order.status === "shipped"
                                ? "75%"
                                : "100%",
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Total & Actions */}
                  <div className="flex items-center justify-between pt-3 border-t border-stone-800">
                    <div>
                      <p className="text-xs text-stone-400">총 금액</p>
                      <p className="text-lg font-bold text-stone-100">{order.total}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        Show
                        상세보기
                      </Button>
                      {order.status === "delivered" && (
                        <Button variant="outline" size="sm">
                          Download
                          영수증
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Empty State */}
        {filteredOrders.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <Package className="mx-auto h-12 w-12 text-stone-700" />
              <p className="mt-4 text-stone-400">해당 상태의 주문이 없습니다</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
