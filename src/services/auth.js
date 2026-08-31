import { mockUser } from '../mock/data'

export const authService = {
  async login(payload) {
    const { username, password } = payload
    if (username === 'demo' && password === '123456') {
      return { data: { user: mockUser, token: 'demo-token' } }
    }
    return { data: { user: null, token: null, message: 'نام کاربری یا رمز عبور نامعتبر است.' } }
  },

  async getCurrentUser() {
    return { data: { user: mockUser } }
  },
}

export default authService
