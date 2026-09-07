import axios from 'axios'
import api from './api'

const baseURL = api.defaults.baseURL

export const realAuthService = {
    async requestLoginOtp(phone) {
        const response = await api.post('/auth/request-login-otp/', {phone_number: phone})
        return {
            ok: true,
            challengeId: response.data.challenge_id,
            phone: response.data.phone_number,
            expiresIn: 180,
            resendAvailableIn: 120,
            account_exists: response.data.account_exists,
            next_step: response.data.next_step,
        }
    },

    async requestRegistrationOtp(phone) {
        const response = await api.post('/auth/request-registration-otp/', {phone_number: phone})
        return {
            ok: true,
            challengeId: response.data.challenge_id,
            phone: response.data.phone_number,
            expiresIn: 180,
            resendAvailableIn: 120,
        }
    },

    async requestPasswordResetOtp(phone) {
        const response = await api.post('/auth/request-password-reset-otp/', {phone_number: phone})
        return {
            ok: true,
            challengeId: response.data.challenge_id,
            phone: response.data.phone_number,
            expiresIn: 180,
            resendAvailableIn: 120,
        }
    },

    async verifyOtp(challengeId, otp) {
        const response = await api.post('/auth/verify-otp/', {
            challenge_id: challengeId,
            otp,
        })

        return {
            ok: true,
            flowToken: response.data.flow_token,
            nextStep: response.data.next_step,
            expiresIn: response.data.expires_in,
        }
    },

    async verifyLoginPassword(flowToken, password) {
        const response = await api.post('/auth/login/verify-password/', {
            flow_token: flowToken,
            password,
        })

        return {
            ok: true,
            access: response.data.access,
            refresh: response.data.refresh,
            user: response.data.user,
        }
    },

    async registerWithPassword(flowToken, password, confirmPassword) {
        const response = await api.post('/auth/register/set-password/', {
            flow_token: flowToken,
            password,
            confirm_password: confirmPassword,
        })

        return {
            ok: true,
            access: response.data.access,
            refresh: response.data.refresh,
            user: response.data.user,
        }
    },

    async resetPassword(flowToken, password, confirmPassword) {
        const response = await api.post('/auth/reset-password/', {
            flow_token: flowToken,
            password,
            confirm_password: confirmPassword,
        })

        return {
            ok: true,
            message: response.data.detail || 'رمز عبور با موفقیت تغییر کرد.',
        }
    },

    async getCurrentUser() {
        return api.get('/auth/me/')
    },

    async refresh(refreshToken) {
        const response = await axios.post(`${baseURL}/auth/refresh/`, {
            refresh: refreshToken,
        }, {
            headers: {
                'Content-Type': 'application/json',
            },
        })

        return {
            access: response.data.access,
            refresh: response.data.refresh,
        }
    },

    async logout(refreshToken) {
        if (!refreshToken) {
            return {
                message: 'Logged out successfully.',
            }
        }

        const response = await axios.post(`${baseURL}/auth/logout/`, {
            refresh: refreshToken,
        }, {
            headers: {
                'Content-Type': 'application/json',
            },
        })

        return {
            message: response.data?.detail || 'خروج با موفقیت انجام شد.',
        }
    },
}

export default realAuthService