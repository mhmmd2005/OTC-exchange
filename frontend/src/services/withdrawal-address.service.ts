import type {
    WithdrawalAddress,
    WithdrawalAddressConfirmInput,
    WithdrawalAddressCreateInput,
    WithdrawalAddressCreateResponse,
} from '@/types'
import {api, ApiError, resolveApi} from './api'
import {mockWithdrawalAddressService} from './mock/withdrawal-address.service'

export interface WithdrawalAddressService {
    list(): Promise<WithdrawalAddress[]>

    create(
        input: WithdrawalAddressCreateInput,
    ): Promise<WithdrawalAddressCreateResponse>

    confirm(
        id: string,
        input: WithdrawalAddressConfirmInput,
    ): Promise<WithdrawalAddress>

    resendConfirmation(
        id: string,
    ): Promise<WithdrawalAddressCreateResponse>

    remove(id: string): Promise<void>

    setDefault(id: string): Promise<WithdrawalAddress>
}

export const withdrawalAddressService: WithdrawalAddressService = {
    list() {
        return resolveApi(
            () => mockWithdrawalAddressService.list(),
            async () => {
                const response =
                    await api.get<{
                        count: number
                        next: string | null
                        previous: string | null
                        results: WithdrawalAddress[]
                    }>('/withdrawals/addresses')

                return response.results
            },
        )
    },

    create(input) {
        return resolveApi(
            () => mockWithdrawalAddressService.create(input),
            () =>
                api.post<WithdrawalAddressCreateResponse>(
                    '/withdrawals/addresses',
                    input,
                ),
        )
    },

    confirm(id, input) {
        return resolveApi(
            () => mockWithdrawalAddressService.confirm(id, input),
            () =>
                api.post<WithdrawalAddress>(
                    `/withdrawals/addresses/${id}/confirm`,
                    input,
                ),
        )
    },

    resendConfirmation(id) {
        return resolveApi(
            () => mockWithdrawalAddressService.resendConfirmation(id),
            () =>
                api.post<WithdrawalAddressCreateResponse>(
                    `/withdrawals/addresses/${id}/resend-confirmation`,
                ),
        )
    },

    remove(id) {
        return resolveApi(
            () => mockWithdrawalAddressService.remove(id),
            () =>
                api.delete<void>(
                    `/withdrawals/addresses/${id}`,
                ),
        )
    },

    setDefault(id) {
        return resolveApi(
            () => mockWithdrawalAddressService.setDefault(id),
            () =>
                api.post<WithdrawalAddress>(
                    `/withdrawals/addresses/${id}/set-default`,
                ),
        )
    },
}

export {ApiError}