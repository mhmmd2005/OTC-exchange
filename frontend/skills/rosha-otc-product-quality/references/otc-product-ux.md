# OTC product UX pass

Optimize for the user's immediate understanding of «می‌پردازم» and «دریافت می‌کنم».

- Keep buy and sell structurally consistent: asset, pay, receive, quick amount, rate, fee, limit, quote validity, review, confirmation, result.
- Show the final received amount, fee, destination/source, and price validity before confirmation. Never silently refresh a reviewed quote.
- Use natural Persian action labels that include the asset where useful, such as «ادامه خرید تتر».
- Preserve idempotency and server-authoritative estimates; UI changes must not recompute canonical financial values with floating-point math.
- Expiry, validation, and transport errors need a clear recovery action and must retain safe user input where possible.
- Test buy and sell through review and success/cancellation states, including keyboard and narrow mobile use.
