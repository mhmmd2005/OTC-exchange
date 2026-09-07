import type { PortfolioValuePoint, PricePoint } from '@/types'
import { addDecimal, multiplyDecimal } from './decimal'

export interface PortfolioAssetHistory {
  total: string
  points: PricePoint[]
}

/**
 * Derive portfolio values without floating-point arithmetic. Series are aligned
 * by their latest common number of samples because the market history contract
 * returns every requested asset at the same period and cadence.
 */
export function buildPortfolioValueHistory(
  tomanBalance: string,
  histories: PortfolioAssetHistory[],
): PortfolioValuePoint[] {
  if (!histories.length) return []
  const pointCount = Math.min(...histories.map((history) => history.points.length))
  if (pointCount < 2) return []

  const referencePoints = histories[0].points.slice(-pointCount)
  return referencePoints.map((referencePoint, index) => {
    let cryptoValue = '0'
    for (const history of histories) {
      const alignedPoint = history.points[history.points.length - pointCount + index]
      cryptoValue = addDecimal(cryptoValue, multiplyDecimal(history.total, alignedPoint.priceToman))
    }
    return {
      timestamp: referencePoint.timestamp,
      valueToman: addDecimal(tomanBalance, cryptoValue),
    }
  })
}
