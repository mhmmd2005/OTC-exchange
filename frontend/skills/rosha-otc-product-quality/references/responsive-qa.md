# Responsive QA pass

Visually and programmatically inspect these viewports:

- 320×568, 360×800, 375×812, 390×844, 414×896, 430×932
- 768×1024, 1024×768
- 1280×800, 1366×768, 1440×900, 1920×1080

Cover dashboard, trade, markets/detail, wallet/detail, Toman and crypto deposit/withdraw, orders/detail, transactions/detail, bank accounts/add, KYC, notifications, support/ticket, profile, security, settings, login, register, OTP, and forgot password.

Fail a case for body horizontal overflow, clipped financial values, colliding labels, unusable controls, content hidden by navigation/sticky actions, unintended desktop tables on mobile, runtime errors, or route mismatch.

Give 375px, 430px, 1440px, and 1920px explicit visual inspection. Use bounded content widths on large displays and purpose-built stacked content on narrow displays.
