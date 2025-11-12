import { NextRequest, NextResponse } from 'next/server'
import { findUserByEmail, addUser, getUserCount } from '@/lib/userDatabase'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, phone, password } = body

    // Validate input
    if (!name || !email || !phone || !password) {
      return NextResponse.json(
        { message: '필수 정보를 모두 입력해주세요' },
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

    // Check if user already exists in shared database
    const existingUser = findUserByEmail(email)
    if (existingUser) {
      return NextResponse.json(
        { message: '이미 존재하는 이메일입니다' },
        { status: 409 }
      )
    }

    // Create new user (default role: customer)
    const newUser = {
      id: String(getUserCount() + 1),
      email,
      phone,
      password, // In production, hash this with bcrypt!
      name,
      role: 'customer',
      level: 3,
      createdAt: new Date().toISOString(),
    }

    // Add to shared database
    addUser(newUser)

    // Generate mock JWT token
    const token = Buffer.from(
      JSON.stringify({ userId: newUser.id, email: newUser.email, role: newUser.role })
    ).toString('base64')

    // Return success response
    return NextResponse.json({
      access_token: token,
      token_type: 'Bearer',
      user: {
        id: newUser.id,
        email: newUser.email,
        name: newUser.name,
        phone: newUser.phone,
        role: newUser.role,
        level: newUser.level,
      },
      message: '회원가입이 완료되었습니다',
    })
  } catch (error) {
    console.error('Registration error:', error)
    return NextResponse.json(
      { message: '회원가입 처리 중 오류가 발생했습니다' },
      { status: 500 }
    )
  }
}
