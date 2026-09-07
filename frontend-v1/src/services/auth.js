import {isMockMode} from './mode'
import {realAuthService} from './realAuth'
import {mockAuthService} from './mockAuth'

function getService() {
    return isMockMode()
        ? mockAuthService
        : realAuthService
}

export const authService = {
    async requestLoginOtp(phone) {
        return getService().requestLoginOtp(phone)
    },

    async requestRegistrationOtp(phone) {
        return getService().requestRegistrationOtp(phone)
    },

    async requestPasswordResetOtp(phone) {
        return getService().requestPasswordResetOtp(phone)
    },

    async verifyOtp(challengeId, otp) {
        return getService().verifyOtp(
            challengeId,
            otp,
        )
    },

    async verifyLoginPassword(
        flowToken,
        password,
    ) {
        return getService().verifyLoginPassword(
            flowToken,
            password,
        )
    },

    async registerWithPassword(
        flowToken,
        password,
        confirmPassword,
    ) {
        return getService().registerWithPassword(
            flowToken,
            password,
            confirmPassword,
        )
    },

    async resetPassword(
        flowToken,
        password,
        confirmPassword,
    ) {
        return getService().resetPassword(
            flowToken,
            password,
            confirmPassword,
        )
    },

    async getCurrentUser() {
        return getService().getCurrentUser()
    },

    async refresh(refreshToken) {
        return getService().refresh(
            refreshToken,
        )
    },

    async logout(refreshToken) {
        return getService().logout(
            refreshToken,
        )
    },
}

export default authService