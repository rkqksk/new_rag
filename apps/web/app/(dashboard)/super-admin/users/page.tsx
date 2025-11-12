"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface User {
  id: string
  name: string
  email: string
  role: string
  status: string
  created_at: string
}

export default function UsersPage() {
  const [searchQuery, setSearchQuery] = useState("")

  // Mock data - 실제로는 API에서 가져올 데이터
  const users: User[] = [
    { id: "1", name: "김철수", email: "kim@example.com", role: "super-admin", status: "active", created_at: "2025-11-01" },
    { id: "2", name: "이영희", email: "lee@example.com", role: "admin", status: "active", created_at: "2025-11-02" },
    { id: "3", name: "박민수", email: "park@example.com", role: "staff", status: "active", created_at: "2025-11-03" },
    { id: "4", name: "최지영", email: "choi@example.com", role: "customer-vip", status: "active", created_at: "2025-11-04" },
    { id: "5", name: "정대현", email: "jung@example.com", role: "customer", status: "inactive", created_at: "2025-11-05" },
  ]

  const filteredUsers = users.filter(
    user =>
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.role.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "super-admin": return "bg-purple-900 text-purple-100"
      case "admin": return "bg-blue-900 text-blue-100"
      case "staff": return "bg-amber-900 text-amber-100"
      case "customer-vip": return "bg-green-900 text-green-100"
      default: return "bg-stone-800 text-stone-300"
    }
  }

  return (
    <div>
      <Navbar title="사용자 관리" subtitle="전체 사용자 및 권한 관리" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">총 사용자</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">{users.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">활성 사용자</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">
                {users.filter(u => u.status === "active").length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">관리자</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">
                {users.filter(u => u.role.includes("admin")).length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-stone-400">VIP 고객</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-stone-100">
                {users.filter(u => u.role === "customer-vip").length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* User List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>사용자 목록</CardTitle>
                <CardDescription>모든 시스템 사용자 관리</CardDescription>
              </div>
              <Button>새 사용자 추가</Button>
            </div>
            <div className="mt-4">
              <Input
                placeholder="사용자 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="max-w-md"
              />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center gap-4 rounded-lg bg-stone-950 p-4 transition-colors hover:bg-stone-900"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-stone-800 text-lg font-semibold text-stone-100">
                    {user.name.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-stone-100">{user.name}</p>
                    <p className="text-xs text-stone-500">{user.email}</p>
                  </div>
                  <Badge className={getRoleBadgeColor(user.role)}>
                    {user.role}
                  </Badge>
                  <Badge variant={user.status === "active" ? "default" : "secondary"}>
                    {user.status}
                  </Badge>
                  <span className="text-xs text-stone-500">{user.created_at}</span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost">편집</Button>
                    <Button size="sm" variant="ghost">삭제</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
