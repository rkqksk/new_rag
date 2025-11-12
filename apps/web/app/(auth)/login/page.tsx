"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const response = await fetch("/api/v1/saas/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.message || "로그인 실패")
      }

      const data = await response.json()

      // Store token and user info
      localStorage.setItem("token", data.access_token)
      localStorage.setItem("user", JSON.stringify(data.user))

      // Redirect based on role
      switch (data.user.role) {
        case "super-user":
          router.push("/super-admin")
          break
        case "admin":
        case "manager":
          router.push("/admin")
          break
        case "staff":
        case "operator":
          router.push("/staff")
          break
        case "customer-vip":
        case "customer":
          router.push("/customer")
          break
        default:
          router.push("/")
      }
    } catch (err: any) {
      setError(err.message || "로그인 중 오류가 발생했습니다.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="w-full max-w-md">
        <Card>
          <CardHeader>
            <CardTitle className="text-center">로그인</CardTitle>
            <CardDescription className="text-center">이메일과 비밀번호를 입력하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">이메일</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="user@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">비밀번호</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              {error && (
                <div className="rounded-md border border-red-900 bg-red-950 p-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "로그인 중..." : "로그인"}
              </Button>

              <div className="mt-4 flex items-center justify-between text-sm">
                <Link href="/forgot-password" className="text-stone-400 hover:text-stone-300">
                  비밀번호 찾기
                </Link>
                <Link href="/register" className="text-stone-400 hover:text-stone-300">
                  회원가입
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
