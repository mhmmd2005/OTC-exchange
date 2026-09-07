import { mockMarketPrices, mockChartSeries } from '../mock/data'

export const marketService = {
  async getPrices() { return { data: mockMarketPrices } },
  async getChartSeries() { return { data: mockChartSeries } },
}

export default marketService
