import { NextRequest, NextResponse } from 'next/server'
import { findUserByEmail } from '@/lib/userDatabase'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email, password } = body

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { message: '이메일과 비밀번호를 입력해주세요' },
        { status: 400 }
      )
    }

    // Find user from shared database
    const user = findUserByEmail(email)

    if (!user) {
      return NextResponse.json(
        { message: '존재하지 않는 사용자입니다' },
        { status: 401 }
      )
    }

    // Verify password
    if (user.password !== password) {
      return NextResponse.json(
        { message: '비밀번호가 일치하지 않습니다' },
        { status: 401 }
      )
    }

    // Generate mock JWT token
    const token = Buffer.from(
      JSON.stringify({ userId: user.id, email: user.email, role: user.role })
    ).toString('base64')

    // Return success response
    return NextResponse.json({
      access_token: token,
      token_type: 'Bearer',
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        phone: user.phone,
        role: user.role,
        level: user.level,
      },
    })
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { message: '로그인 처리 중 오류가 발생했습니다' },
      { status: 500 }
    )
  }
}
