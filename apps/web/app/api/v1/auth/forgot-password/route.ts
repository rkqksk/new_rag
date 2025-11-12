import { NextRequest, NextResponse } from 'next/server'

// Mock user database
const users = [
  { id: '1', email: 'super@example.com', name: 'Super User' },
  { id: '2', email: 'admin@example.com', name: 'Admin User' },
  { id: '3', email: 'staff@example.com', name: 'Staff User' },
  { id: '4', email: 'customer@example.com', name: 'Customer User' },
]

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email } = body

    // Validate input
    if (!email) {
      return NextResponse.json(
        { message: '이메일을 입력해주세요' },
        { status: 400 }
      )
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { message: '올바른 이메일 형식이 아닙니다' },
        { status: 400 }
      )
    }

    // Check if user exists
    const user = users.find(u => u.email === email)

    // Always return success to prevent email enumeration attacks
    // In production, actually send reset email here

    if (user) {
      console.log(`[Mock] Password reset email sent to: ${email}`)
      // In production: send email with reset token
      // await sendPasswordResetEmail(email, resetToken)
    } else {
      console.log(`[Mock] User not found, but returning success: ${email}`)
    }

    return NextResponse.json({
      message: '비밀번호 재설정 링크가 이메일로 전송되었습니다',
      email: email,
    })
  } catch (error) {
    console.error('Forgot password error:', error)
    return NextResponse.json(
      { message: '요청 처리 중 오류가 발생했습니다' },
      { status: 500 }
    )
  }
}
