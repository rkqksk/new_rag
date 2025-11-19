"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

export interface Notification {
  id: string
  type: "info" | "success" | "warning" | "error"
  title: string
  message: string
  timestamp: string
  read: boolean
  action_url?: string
  action_label?: string
}

interface NotificationCenterProps {
  className?: string
}

// Mock notifications
const mockNotifications: Notification[] = [
  {
    id: "notif_1",
    type: "success",
    title: "크롤링 완료",
    message: "Product Catalog 크롤링이 성공적으로 완료되었습니다. 150개 항목이 수집되었습니다.",
    timestamp: "2025-11-08T14:30:00Z",
    read: false,
    action_url: "/admin/crawling",
    action_label: "결과 보기"
  },
  {
    id: "notif_2",
    type: "warning",
    title: "Rate Limit 경고",
    message: "API 호출이 일일 한도의 85%에 도달했습니다. 한도 초과 시 추가 요금이 발생합니다.",
    timestamp: "2025-11-08T14:15:00Z",
    read: false,
    action_url: "/admin/analytics",
    action_label: "사용량 확인"
  },
  {
    id: "notif_3",
    type: "info",
    title: "새로운 기능 출시",
    message: "Webhook 시스템이 추가되었습니다. 이제 크롤링 완료 시 자동 알림을 받을 수 있습니다.",
    timestamp: "2025-11-08T13:45:00Z",
    read: false,
    action_url: "/admin/webhooks",
    action_label: "설정하기"
  },
  {
    id: "notif_4",
    type: "error",
    title: "크롤링 실패",
    message: "MSDS Documents 크롤링 중 오류가 발생했습니다: Connection timeout",
    timestamp: "2025-11-08T13:20:00Z",
    read: true,
    action_url: "/admin/crawling",
    action_label: "재시도"
  },
  {
    id: "notif_5",
    type: "success",
    title: "결제 완료",
    message: "Pro 플랜 구독이 성공적으로 갱신되었습니다. 다음 결제일은 2025-12-08입니다.",
    timestamp: "2025-11-08T12:00:00Z",
    read: true,
    action_url: "/admin/billing",
    action_label: "영수증 보기"
  },
]

export function NotificationCenter({ className }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications)
  const [isOpen, setIsOpen] = useState(false)
  const [filter, setFilter] = useState<"all" | "unread">("all")

  const unreadCount = notifications.filter(n => !n.read).length

  const filteredNotifications = filter === "all"
    ? notifications
    : notifications.filter(n => !n.read)

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
    toast.success("알림을 읽음으로 표시했습니다")
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    toast.success("모든 알림을 읽음으로 표시했습니다")
  }

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
    toast.success("알림이 삭제되었습니다")
  }

  const clearAll = () => {
    setNotifications([])
    toast.success("모든 알림이 삭제되었습니다")
  }

  const getIcon = (type: Notification["type"]) => {
    switch (type) {
      case "success":
        return <span className="text-green-400 font-bold">✓</span>
      case "warning":
        return <span className="text-yellow-400 font-bold">⚠</span>
      case "error":
        return <span className="text-red-400 font-bold">✕</span>
      case "info":
      default:
        return <span className="text-blue-400 font-bold">ⓘ</span>
    }
  }

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diff = now.getTime() - time.getTime()

    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (days > 0) return `${days}일 전`
    if (hours > 0) return `${hours}시간 전`
    if (minutes > 0) return `${minutes}분 전`
    return "방금 전"
  }

  return (
    <div className={cn("relative", className)}>
      {/* Bell Icon Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="relative"
      >
        <span className="text-lg">{unreadCount > 0 ? "Notifications" : "No notifications"}</span>
        {unreadCount > 0 && (
          <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center bg-red-600 text-white text-xs">
            {unreadCount > 9 ? "9+" : unreadCount}
          </Badge>
        )}
      </Button>

      {/* Notification Panel */}
      {isOpen && (
        <Card className="absolute right-0 top-12 w-96 max-h-[600px] overflow-hidden shadow-lg border-stone-800 bg-stone-950 z-50">
          {/* Header */}
          <div className="p-4 border-b border-stone-800">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-stone-100">알림</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8"
              >
                ×
              </Button>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2">
              <Button
                variant={filter === "all" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilter("all")}
                className="flex-1"
              >
                전체 ({notifications.length})
              </Button>
              <Button
                variant={filter === "unread" ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilter("unread")}
                className="flex-1"
              >
                읽지 않음 ({unreadCount})
              </Button>
            </div>
          </div>

          {/* Actions */}
          {notifications.length > 0 && (
            <div className="p-2 border-b border-stone-800 flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={markAllAsRead}
                className="flex-1 text-xs"
                disabled={unreadCount === 0}
              >
                모두 읽음
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAll}
                className="flex-1 text-xs text-red-400 hover:text-red-300"
              >
                모두 삭제
              </Button>
            </div>
          )}

          {/* Notifications List */}
          <div className="overflow-y-auto max-h-[450px]">
            {filteredNotifications.length === 0 ? (
              <div className="p-8 text-center text-stone-500">
                <p className="text-sm">알림이 없습니다</p>
              </div>
            ) : (
              <div className="divide-y divide-stone-800">
                {filteredNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={cn(
                      "p-4 hover:bg-stone-900 transition-colors",
                      !notification.read && "bg-stone-900/50"
                    )}
                  >
                    <div className="flex gap-3">
                      {/* Icon */}
                      <div className="flex-shrink-0 mt-0.5">
                        {getIcon(notification.type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className={cn(
                            "text-sm font-medium",
                            !notification.read ? "text-stone-100" : "text-stone-300"
                          )}>
                            {notification.title}
                          </h4>
                          {!notification.read && (
                            <div className="h-2 w-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />
                          )}
                        </div>

                        <p className="text-xs text-stone-400 mt-1 line-clamp-2">
                          {notification.message}
                        </p>

                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-stone-500">
                            {getTimeAgo(notification.timestamp)}
                          </span>

                          <div className="flex gap-1">
                            {notification.action_url && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 px-2 text-xs text-blue-400 hover:text-blue-300"
                                onClick={() => {
                                  markAsRead(notification.id)
                                  // Navigate to action_url
                                  toast.info(`이동: ${notification.action_url}`)
                                }}
                              >
                                {notification.action_label}
                              </Button>
                            )}
                            {!notification.read && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => markAsRead(notification.id)}
                                title="읽음으로 표시"
                              >
                                ✓
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 text-red-400 hover:text-red-300"
                              onClick={() => deleteNotification(notification.id)}
                              title="삭제"
                            >
                              ×
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}
