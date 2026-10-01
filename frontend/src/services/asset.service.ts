import type {AssetNetwork, AssetSymbol} from '@/types'
import {api} from './api'

export interface AssetCatalogItem {
    id: string
    symbol: AssetSymbol
    nameFa: string
    nameEn: string
    iconUrl?: string
    color: string
    tradable: boolean
    depositEnabled: boolean
    withdrawalEnabled: boolean
    networks: AssetNetwork[]
    updatedAt: string
}

interface AssetListResponse {
    count: number
    next: string | null
    previous: string | null
    results: AssetCatalogItem[]
}

export interface AssetService {
    list(): Promise<AssetCatalogItem[]>

    getBySymbol(symbol: AssetSymbol): Promise<AssetCatalogItem>

    getNetworks(symbol: AssetSymbol): Promise<AssetNetwork[]>
}

export const assetService: AssetService = {
    async list() {
        const response =
            await api.get<AssetListResponse>(
                '/assets/',
            )

        return response.results
    },

    getBySymbol(symbol) {
        return api.get<AssetCatalogItem>(
            `/assets/${symbol}/`,
        )
    },

    getNetworks(symbol) {
        return api.get<AssetNetwork[]>(
            `/assets/${symbol}/networks/`,
        )
    },
}

export default assetService