---
name: rosha-otc-product-quality
description: Audit and refine the Rosha Persian OTC customer frontend across product UX, design-system, mobile/PWA, charts, financial forms, responsive QA, and RTL. Use only for this repository's end-to-end product quality work; preserve OTC business flows and keep /style read-only.
---

# Rosha OTC Product Quality

Use this skill for system-wide UI/UX refinement of the customer application in this repository.

## Product invariants

- The product is exchange-counterparty OTC only. Never introduce P2P, an order book, maker/taker, spot-terminal, margin, leverage, or futures concepts.
- Preserve routes, stores, API contracts, authentication, KYC, wallet, quote, order, deposit, and withdrawal behavior unless the task explicitly authorizes a logic change.
- Keep the customer interface Persian and RTL. Isolate Latin financial identifiers with reusable mixed-direction primitives.
- Treat `/style` as read-only engineering reference and do not visually copy it.
- Prefer existing shared components and dependencies. Add a dependency only when it solves a demonstrated product problem.
- Never offline-cache authenticated financial or identity data.

## Specialist routing

Read every reference required by the requested scope:

- Buy/sell, quote, review, limits, and recovery: [OTC product UX](references/otc-product-ux.md)
- Tokens, components, hierarchy, and visual identity: [FinTech design system](references/fintech-design-system.md)
- Mobile shell, bottom navigation, sticky actions, and PWA: [Mobile FinTech UX](references/mobile-fintech-ux.md)
- Portfolio charts, sparklines, tooltips, and chart states: [Financial data visualization](references/financial-data-visualization.md)
- Amount, bank, wallet, OTP, KYC, and validation forms: [Financial forms](references/financial-forms.md)
- Route and breakpoint verification: [Responsive QA](references/responsive-qa.md)
- Persian directionality and mixed financial content: [RTL quality](references/rtl-quality.md)

## Completion evidence

Judge the rendered application, not CSS alone. Run the repository's configured typecheck/tests/build, inspect browser console output, exercise the affected financial flows, and capture responsive evidence proportional to the change.
