"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess(false)

    try {
      const response = await fetch("/api/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.message || "비밀번호 재설정 요청 실패")
      }

      setSuccess(true)
    } catch (err: any) {
      setError(err.message || "요청 중 오류가 발생했습니다.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-black px-4">
      <div className="w-full max-w-md">
        <Card>
          <CardHeader>
            <CardTitle className="text-center">비밀번호 찾기</CardTitle>
            <CardDescription className="text-center">
              등록된 이메일 주소를 입력하시면 비밀번호 재설정 링크를 보내드립니다
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
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

              {error && (
                <div className="rounded-md border border-red-900 bg-red-950 p-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              {success && (
                <div className="rounded-md border border-green-900 bg-green-950 p-3 text-sm text-green-400">
                  이메일이 발송되었습니다!
                </div>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "전송 중..." : "비밀번호 재설정 링크 받기"}
              </Button>

              <div className="mt-4 text-center text-sm">
                <Link href="/login" className="text-stone-400 hover:text-stone-300">
                  ← 로그인으로 돌아가기
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
