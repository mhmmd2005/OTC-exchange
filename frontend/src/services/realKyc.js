import api from './api'

function buildFormData(data) {
    const formData = new FormData()

    formData.append('first_name', data.first_name || '')
    formData.append('last_name', data.last_name || '')
    formData.append('national_id', data.national_id || '')
    formData.append('birth_date', data.birth_date || '')
    formData.append('email', data.email || '')

    if (data.identity_document instanceof File) {
        formData.append('identity_document', data.identity_document)
    }

    return formData
}

export const realKycService = {
    async get() {
        return api.get('/kyc/')
    },

    async submit(data) {
        return api.post('/kyc/submit/', buildFormData(data))
    },

    async update(data) {
        return api.patch('/kyc/update/', buildFormData(data))
    },

    async status() {
        return api.get('/kyc/status/')
    },
}

export default realKycService