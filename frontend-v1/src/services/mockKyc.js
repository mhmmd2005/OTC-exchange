const STORAGE_KEY = 'otc-mock-kyc'

const defaultKyc = {
    id: 1,
    first_name: '',
    last_name: '',
    national_id: '',
    birth_date: '',
    phone_number: '+989123456780',
    email: '',
    identity_document: null,
    status: 'not_started',
    status_label: 'تکمیل نشده',
    rejection_reason: '',
    submitted_at: null,
    reviewed_at: null,
    can_edit: true,
    can_submit: true,
}

function load() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {...defaultKyc}
    } catch {
        return {...defaultKyc}
    }
}

function save(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    return data
}

function delay(ms = 250) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

function normalizeFile(file) {
    if (!(file instanceof File)) return file || null

    return {
        name: file.name,
        type: file.type,
        size: file.size,
        mock: true,
    }
}

export const mockKycService = {
    async get() {
        await delay()
        return {data: load()}
    },

    async status() {
        await delay()
        return {data: load()}
    },

    async submit(data) {
        await delay()

        const current = load()

        const payload = {
            ...current,
            ...data,
            identity_document: normalizeFile(data.identity_document),
            status: 'pending',
            status_label: 'در انتظار بررسی',
            rejection_reason: '',
            submitted_at: new Date().toISOString(),
            can_edit: false,
            can_submit: false,
        }

        return {data: save(payload)}
    },

    async update(data) {
        await delay()

        const current = load()

        const payload = {
            ...current,
            ...data,
            identity_document: data.identity_document
                ? normalizeFile(data.identity_document)
                : current.identity_document,
        }

        return {data: save(payload)}
    },
}

export default mockKycService