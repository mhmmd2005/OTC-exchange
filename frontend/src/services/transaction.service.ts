import type {PaginatedResult, Transaction, TransactionFilters,} from '@/types'
import {api, ApiError, resolveApi,} from './api'
import {normalizedSearch, paginate,} from './mock/helpers'
import {mockDb} from './mock/state'

export interface TransactionService {
    list(
        filters?: TransactionFilters,
    ): Promise<PaginatedResult<Transaction>>

    getById(
        id: string,
    ): Promise<Transaction>
}

function normalizeId(value: string): string {
    return value.trim()
}

export const transactionService: TransactionService = {
    list(filters = {}) {
        return resolveApi(
            () => {
                const search =
                    normalizedSearch(filters.search)

                const from = filters.from
                    ? Date.parse(filters.from)
                    : Number.NEGATIVE_INFINITY

                const to = filters.to
                    ? Date.parse(filters.to)
                    : Number.POSITIVE_INFINITY

                const filtered =
                    mockDb.transactions.filter(
                        (transaction) => {
                            const timestamp =
                                Date.parse(
                                    transaction.createdAt,
                                )

                            const matchesSearch =
                                !search
                                || transaction.referenceNumber
                                    .toLocaleLowerCase('fa')
                                    .includes(search)
                                || transaction.title
                                    .toLocaleLowerCase('fa')
                                    .includes(search)
                                || Boolean(
                                    transaction.txId
                                        ?.toLocaleLowerCase(
                                            'fa',
                                        )
                                        .includes(search),
                                )
                                || Boolean(
                                    transaction.orderId
                                        ?.toLocaleLowerCase(
                                            'fa',
                                        )
                                        .includes(search),
                                )

                            return (
                                (!filters.type
                                    || transaction.type
                                    === filters.type)
                                && (
                                    !filters.status
                                    || transaction.status
                                    === filters.status
                                )
                                && (
                                    !filters.assetSymbol
                                    || transaction.assetSymbol
                                        .toUpperCase()
                                    === filters.assetSymbol
                                        .toUpperCase()
                                )
                                && (
                                    !filters.networkCode
                                    || transaction.networkCode
                                        ?.toUpperCase()
                                    === filters.networkCode
                                        .toUpperCase()
                                )
                                && timestamp >= from
                                && timestamp <= to
                                && matchesSearch
                            )
                        },
                    )

                filtered.sort(
                    (a, b) =>
                        Date.parse(b.createdAt)
                        - Date.parse(a.createdAt),
                )

                return paginate(
                    filtered,
                    filters,
                )
            },

            () =>
                api.get<
                    PaginatedResult<Transaction>
                >('/transactions/', {
                    query: {
                        page: filters.page,
                        pageSize: filters.pageSize,
                        type: filters.type,
                        status: filters.status,
                        asset: filters.assetSymbol,
                        network: filters.networkCode,
                        from: filters.from,
                        to: filters.to,
                        search: filters.search,
                    },
                }),
        )
    },

    getById(id) {
        const normalizedId =
            normalizeId(id)

        if (!normalizedId) {
            throw new ApiError(
                'شناسه تراکنش معتبر نیست.',
                'BAD_REQUEST',
                400,
            )
        }

        return resolveApi(
            () => {
                const transaction =
                    mockDb.transactions.find(
                        (item) =>
                            item.id === normalizedId
                            || item.referenceNumber
                            === normalizedId,
                    )

                if (!transaction) {
                    throw new ApiError(
                        'تراکنش مورد نظر پیدا نشد.',
                        'NOT_FOUND',
                        404,
                    )
                }

                return transaction
            },

            () =>
                api.get<Transaction>(
                    `/transactions/${encodeURIComponent(
                        normalizedId,
                    )}/`,
                ),
        )
    },
}

export default transactionService