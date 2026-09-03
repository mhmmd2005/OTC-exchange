export const currency = (value, code = 'IRR') => {
  const num = Number(value || 0)
  return new Intl.NumberFormat('fa-IR', {
    maximumFractionDigits: code === 'USDT' ? 2 : 0,
    minimumFractionDigits: code === 'USDT' ? 2 : 0,
  }).format(num) + ` ${code}`
}

export const compactCurrency = (value, code = 'IRT') => `${new Intl.NumberFormat('fa-IR').format(value)} ${code}`

export const priceFormat = (value) => new Intl.NumberFormat('fa-IR').format(Number(value || 0))

export const dateFormat = (value) => new Date(value).toLocaleDateString('fa-IR', { year: 'numeric', month: 'short', day: 'numeric' })
