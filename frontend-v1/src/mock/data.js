export const mockUser = {
  id: 1,
  username: 'mahdi_gh',
  fullName: 'مهدی قاسمی',
  email: 'mahdi@otc.ir',
  phone: '+۹۸۹۱۲۱۲۳۴۵۶',
  kycStatus: 'تأیید شده',
  kycLevel: 'سطح ۲',
  lastLogin: '۱۴ مرداد ۱۴۰۳ • ۱۰:۴۲',
  avatar: 'MG'
}

export const mockMarketPrices = [
  { pair: 'USDT/IRT', buy: 610500, sell: 608900, change: 3400, pct: 0.56, trend: 'up', status: 'بازار پایدار' },
  { pair: 'BTC/IRT', buy: 4510000000, sell: 4485000000, change: -12000000, pct: -0.27, trend: 'down', status: 'نوسان متوسط' },
  { pair: 'ETH/IRT', buy: 184500000, sell: 183200000, change: 3200000, pct: 1.76, trend: 'up', status: 'خرید قوی' },
  { pair: 'USDT/USD', buy: 1.0, sell: 0.9994, change: 0.0008, pct: 0.08, trend: 'up', status: 'ثبات' },
]

export const mockPortfolio = {
  totalAsset: 12550000000,
  irtBalance: 125500000,
  usdtBalance: 12500.5,
  pnl: 6300000,
  processingOrders: 12
}

export const mockWallets = [
  { id: 'irt', name: 'تومان', symbol: 'IRT', balance: 125500000, available: 123400000, pending: 2100000, address: 'IRT-001-4452-8A6D', network: 'بانک مرکزی' },
  { id: 'usdt', name: 'USDT', symbol: 'USDT', balance: 12500.5, available: 12000, pending: 500.5, address: 'TQ5H8s...', network: 'TRC20' },
  { id: 'btc', name: 'BTC', symbol: 'BTC', balance: 0.84, available: 0.72, pending: 0.12, address: 'bc1q8x...', network: 'Bitcoin' },
  { id: 'eth', name: 'ETH', symbol: 'ETH', balance: 4.2, available: 3.8, pending: 0.4, address: '0xD9E1...2aA', network: 'Ethereum' },
]

export const mockOrders = [
  { id: 'OTC-24082', type: 'خرید', asset: 'USDT', amount: 2500, price: 610500, total: 1526250000, status: 'در انتظار بررسی', time: '۱۴۰۳/۰۵/۲۳ ۱۲:۳۴' },
  { id: 'OTC-24090', type: 'فروش', asset: 'USDT', amount: 9000, price: 608900, total: 5480100000, status: 'در حال پردازش', time: '۱۴۰۳/۰۵/۲۳ ۱۰:۱۲' },
  { id: 'OTC-24108', type: 'خرید', asset: 'BTC', amount: 0.12, price: 4510000000, total: 541200000, status: 'انجام شد', time: '۱۴۰۳/۰۵/۲۲ ۱۸:۴۰' },
  { id: 'OTC-24128', type: 'فروش', asset: 'ETH', amount: 0.8, price: 184500000, total: 147600000, status: 'رد شد', time: '۱۴۰۳/۰۵/۲۱ ۹:۳۵' },
  { id: 'OTC-24140', type: 'خرید', asset: 'USDT', amount: 5000, price: 610500, total: 3052500000, status: 'لغو شد', time: '۱۴۰۳/۰۵/۲۱ ۱۶:۱۸' },
]

export const mockTransactions = [
  { type: 'واریز', asset: 'USDT', amount: 3500, status: 'تأیید شده', id: 'TX-102534', date: '۱۴۰۳/۰۵/۲۳' },
  { type: 'برداشت', asset: 'IRT', amount: 52000000, status: 'در انتظار', id: 'TX-102510', date: '۱۴۰۳/۰۵/۲۳' },
  { type: 'خرید', asset: 'BTC', amount: 0.12, status: 'تأیید شده', id: 'TX-102493', date: '۱۴۰۳/۰۵/۲۲' },
  { type: 'فروش', asset: 'ETH', amount: 0.8, status: 'رد شده', id: 'TX-102438', date: '۱۴۰۳/۰۵/۲۱' },
  { type: 'انتقال', asset: 'USDT', amount: 1500, status: 'تأیید شده', id: 'TX-102413', date: '۱۴۰۳/۰۵/۲۱' },
]

export const mockRecentActivity = [
  { title: 'واریز USDT', amount: '+ ۳۵۰۰ USDT', time: '۲ ساعت قبل' },
  { title: 'برداشت تومان', amount: '- ۵۲,۰۰۰,۰۰۰ تومان', time: '۵ ساعت قبل' },
  { title: 'خرید BTC OTC', amount: '+ ۰.۱۲ BTC', time: 'دیروز' },
  { title: 'تغییر وضعیت KYC', amount: 'تأیید شده', time: '۳ روز قبل' },
]

export const mockTickets = [
  { id: 'TK-1042', subject: 'تأیید واریز اولیه', status: 'در انتظار پاسخ', priority: 'متوسط', updated: '۲ ساعت قبل' },
  { id: 'TK-1038', subject: 'سوال درباره نرخ سفارش', status: 'بسته', priority: 'پایین', updated: '۱ روز قبل' },
  { id: 'TK-1035', subject: 'تغییر روش تسویه', status: 'پاسخ داده شد', priority: 'بالا', updated: '۳ روز قبل' },
]

export const mockKyc = {
  status: 'در انتظار بررسی',
  steps: [
    { title: 'اطلاعات شخصی', status: 'done' },
    { title: 'اطلاعات هویتی', status: 'done' },
    { title: 'آپلود مدارک', status: 'done' },
    { title: 'تأیید اطلاعات', status: 'active' },
    { title: 'نمایش وضعیت', status: 'pending' },
  ]
}

export const mockSecurity = {
  lastLogin: '10:42 • ۱۴ مرداد ۱۴۰۳',
  activeSessions: [
    { device: 'موبایل iPhone 14 Pro', location: 'تهران', ip: '172.16.10.37', status: 'فعال' },
    { device: 'دسکتاپ Chrome', location: 'مشهد', ip: '172.16.10.88', status: 'فعال' },
    { device: 'موبایل Pixel 8', location: 'شیراز', ip: '172.16.10.19', status: 'غیرفعال' },
  ],
  devices: [
    { name: 'دسکتاپ Chrome', os: 'Windows 11', lastSeen: 'همین الان' },
    { name: 'موبایل iPhone 14 Pro', os: 'iOS 17', lastSeen: '۳ دقیقه قبل' }
  ],
  loginHistory: [
    { time: '۱۴ مرداد ۱۴۰۳ • ۱۰:۴۲', ip: '172.16.10.37', location: 'تهران' },
    { time: '۱۳ مرداد ۱۴۰۳ • ۲۲:۱۶', ip: '172.16.10.88', location: 'مشهد' },
    { time: '۱۲ مرداد ۱۴۰۳ • ۰۹:۱۲', ip: '172.16.10.19', location: 'شیراز' }
  ]
}

export const mockChartSeries = {
  usdt: [21, 28, 24, 32, 30, 36, 42],
  assets: [18, 24, 22, 35, 31, 40, 46],
  volume: [14, 18, 17, 24, 22, 28, 30],
  transactions: [8, 12, 15, 14, 18, 20, 22],
}
