import axios from 'axios'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  name: string
  company: string
}

export class AuthService {
  private baseURL: string

  constructor(baseURL: string = process.env.API_URL || 'http://localhost:8001') {
    this.baseURL = baseURL
  }

  async login(credentials: LoginCredentials) {
    const response = await axios.post(`${this.baseURL}/api/v1/auth/login`, credentials)
    return response.data
  }

  async register(data: RegisterData) {
    const response = await axios.post(`${this.baseURL}/api/v1/auth/register`, data)
    return response.data
  }

  async logout() {
    // Clear tokens and user data
    return true
  }

  async refreshToken(token: string) {
    const response = await axios.post(`${this.baseURL}/api/v1/auth/refresh`, { token })
    return response.data
  }
}

export const authService = new AuthService()
