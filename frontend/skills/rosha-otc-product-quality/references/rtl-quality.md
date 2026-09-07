# RTL quality pass

- Keep `html[lang="fa"][dir="rtl"]` and natural Persian reading/order across navigation, tables, pagination, tabs, forms, modals, drawers, and sheets.
- Render symbols, addresses, TXIDs, IBANs, card numbers, OTPs, and Latin financial fragments with explicit LTR isolation (`dir="ltr"`, `bdi`, or a shared primitive).
- Format amounts with a consistent Persian locale while preserving precision and recognizable Latin asset symbols.
- Directional icons describe action/navigation direction in the rendered RTL context; do not mirror universal icons such as search, copy, or visibility.
- Inputs align by semantic content: Persian prose RTL, technical identifiers and numeric codes LTR, mixed amount/unit compositions isolated.
- Test long amounts, decimals, masked identifiers, validation text, and labels at narrow widths. Never hide a meaningful value with ellipsis solely to make a row fit.
