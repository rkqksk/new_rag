"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

interface NavItem {
  title: string
  href: string
  icon: string
  badge?: string
  roles: string[]
}

const navItems: NavItem[] = [
  // Super-user only
  { title: "시스템 개요", href: "/super-admin", icon: "⚡", roles: ["super-user"] },
  { title: "사용자 관리", href: "/super-admin/users", icon: "👥", roles: ["super-user"] },
  { title: "시스템 설정", href: "/super-admin/system", icon: "⚙️", roles: ["super-user"] },
  { title: "감사 로그", href: "/super-admin/logs", icon: "📜", roles: ["super-user"] },

  // Admin + Manager
  { title: "관리 대시보드", href: "/admin", icon: "📊", roles: ["super-user", "admin", "manager"] },
  { title: "웹 크롤링", href: "/admin/crawling", icon: "🌐", roles: ["super-user", "admin", "manager"] },
  { title: "데이터 분석", href: "/admin/analytics", icon: "📈", roles: ["super-user", "admin", "manager"] },
  { title: "결제 관리", href: "/admin/billing", icon: "💰", roles: ["super-user", "admin", "manager"] },
  { title: "API 키 관리", href: "/admin/api-keys", icon: "🔑", roles: ["super-user", "admin"] },

  // Staff + Operator
  { title: "제조 관리", href: "/staff", icon: "🏭", roles: ["super-user", "admin", "staff", "operator"] },
  { title: "품질 관리", href: "/staff/quality", icon: "✅", roles: ["super-user", "admin", "staff", "operator"] },
  { title: "재고 관리", href: "/staff/inventory", icon: "📦", roles: ["super-user", "admin", "staff"] },

  // Everyone
  { title: "제품 검색", href: "/customer/search", icon: "🔍", roles: ["super-user", "admin", "manager", "staff", "operator", "customer-vip", "customer"] },
  { title: "주문 내역", href: "/customer/orders", icon: "📋", roles: ["super-user", "admin", "customer-vip", "customer"] },
  { title: "고객 지원", href: "/customer/support", icon: "💬", roles: ["super-user", "admin", "customer-vip", "customer"] },
]

interface SidebarProps {
  userRole: string
  userName?: string
  userEmail?: string
}

export function Sidebar({ userRole, userName = "User", userEmail = "user@example.com" }: SidebarProps) {
  const pathname = usePathname()

  const filteredNavItems = navItems.filter(item => item.roles.includes(userRole))

  const getRoleDisplay = (role: string) => {
    const roleMap: Record<string, { label: string; color: string }> = {
      "super-user": { label: "Super-user", color: "bg-purple-900 text-purple-100" },
      "admin": { label: "Admin", color: "bg-blue-900 text-blue-100" },
      "manager": { label: "Manager", color: "bg-cyan-900 text-cyan-100" },
      "staff": { label: "Staff", color: "bg-green-900 text-green-100" },
      "operator": { label: "Operator", color: "bg-emerald-900 text-emerald-100" },
      "customer-vip": { label: "VIP", color: "bg-amber-900 text-amber-100" },
      "customer": { label: "Customer", color: "bg-stone-700 text-stone-100" },
    }
    return roleMap[role] || roleMap["customer"]
  }

  const roleDisplay = getRoleDisplay(userRole)

  return (
    <div className="flex h-screen w-64 flex-col border-r border-stone-800 bg-black">
      {/* Header */}
      <div className="p-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="text-2xl">⚡</div>
          <div>
            <h1 className="text-xl font-bold text-stone-100">RAG Enterprise</h1>
            <p className="text-xs text-stone-500">v2.0.0</p>
          </div>
        </Link>
      </div>

      <Separator />

      {/* User Info */}
      <div className="p-4">
        <div className="flex items-center gap-3 rounded-lg bg-stone-950 p-3">
          <Avatar>
            <AvatarFallback className="bg-stone-800 text-stone-100">
              {userName.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 overflow-hidden">
            <p className="truncate text-sm font-medium text-stone-100">{userName}</p>
            <p className="truncate text-xs text-stone-500">{userEmail}</p>
          </div>
        </div>
        <div className="mt-2 flex justify-center">
          <Badge className={roleDisplay.color}>{roleDisplay.label}</Badge>
        </div>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {filteredNavItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-stone-800 text-stone-100"
                  : "text-stone-400 hover:bg-stone-900 hover:text-stone-100"
              )}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="flex-1">{item.title}</span>
              {item.badge && (
                <Badge variant="secondary" className="text-xs">
                  {item.badge}
                </Badge>
              )}
            </Link>
          )
        })}
      </nav>

      <Separator />

      {/* Footer */}
      <div className="p-3">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-stone-400 transition-colors hover:bg-stone-900 hover:text-stone-100"
        >
          <span className="text-lg">⚙️</span>
          <span>설정</span>
        </Link>
        <button
          onClick={() => {
            localStorage.clear()
            window.location.href = "/login"
          }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-stone-400 transition-colors hover:bg-stone-900 hover:text-red-400"
        >
          <span className="text-lg">🚪</span>
          <span>로그아웃</span>
        </button>
      </div>
    </div>
  )
}
