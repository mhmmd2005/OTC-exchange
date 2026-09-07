const STORAGE_KEY = 'otc-mock-kyc'

function load() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
    } catch {
        return null
    }
}

function save(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    return data
}

function delay(ms = 250) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

function normalizeId(id) {
    const value = Number(id)
    return Number.isNaN(value) ? id : value
}

function matchesId(data, id) {
    return data && String(data.id) === String(id)
}

export const mockAdminKycService = {
    async get() {
        await delay()

        const data = load()

        if (!data) {
            return {data: []}
        }

        return {data: [data]}
    },

    async getPending() {
        await delay()

        const data = load()

        if (!data || data.status !== 'pending') {
            return {data: []}
        }

        return {data: [data]}
    },

    async getById(id) {
        await delay()

        const data = load()

        if (!matchesId(data, normalizeId(id))) {
            throw new Error('KYC application not found')
        }

        return {data}
    },

    async approve(id) {
        await delay()

        const current = load()

        if (!matchesId(current, normalizeId(id))) {
            throw new Error('KYC application not found')
        }

        if (current.status !== 'pending') {
            throw new Error('این درخواست در وضعیت قابل تأیید نیست.')
        }

        const payload = {
            ...current,
            status: 'approved',
            status_label: 'تأیید شده',
            rejection_reason: '',
            reviewed_at: new Date().toISOString(),
            can_edit: false,
            can_submit: false,
        }

        return {data: save(payload)}
    },

    async reject(id, reason) {
        await delay()

        const current = load()

        if (!matchesId(current, normalizeId(id))) {
            throw new Error('KYC application not found')
        }

        if (current.status !== 'pending') {
            throw new Error('این درخواست در وضعیت قابل رد نیست.')
        }

        if (!reason || !reason.trim()) {
            throw new Error('دلیل رد درخواست را وارد کنید.')
        }

        const payload = {
            ...current,
            status: 'rejected',
            status_label: 'رد شده',
            rejection_reason: reason.trim(),
            reviewed_at: new Date().toISOString(),
            can_edit: true,
            can_submit: true,
        }

        return {data: save(payload)}
    },
}

export default mockAdminKycService