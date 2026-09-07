# Mobile FinTech UX pass

- Use the authenticated global shell with خانه، خرید/فروش، کیف پول، سفارش‌ها، بیشتر across normal app routes.
- Root headers show page identity plus relevant notification/profile actions. Nested headers show back, title, and at most one contextual action.
- The More action opens grouped account and financial navigation in an accessible sheet/drawer.
- Centralize safe-area, bottom-navigation, and mobile-header spacing in the shell. Page-local arbitrary bottom padding is a defect.
- Sticky trade/KYC/deposit/withdraw actions sit above the bottom navigation and remain usable with the virtual keyboard.
- Prefer one surface with spacing, typography, and dividers over card-in-card nesting.
- Wallet cards stack main amount, approximate Toman value, available/locked metrics, then a 2×2 action grid at narrow widths.
- Use dedicated mobile rows/cards for markets, orders, and transactions; technical details belong on detail screens.
- Respect reduced motion and preserve native-feeling scroll, touch targets, and standalone safe areas.
