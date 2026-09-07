# Financial forms pass

- Standardize label, helper, error, disabled, read-only, focus, prefix/suffix, and icon behavior through shared primitives.
- Normal controls are generally 44–48px; primary amount fields are 52–60px where context supports it.
- Amount entry accepts Persian and English digits, grouping separators, allowed crypto decimals, currency suffix, available balance, Max, quick amounts, validation, and stable cursor behavior.
- Keep server estimates and canonical decimals authoritative. Never use imprecise floating-point arithmetic for committed values.
- Show field-specific errors beside the field; a toast alone is insufficient.
- Bank cards and IBANs are masked in overview surfaces. Reveal/copy only where product policy permits.
- Asset, network, and bank selection on mobile should use an accessible searchable sheet when inline controls become crowded.
- KYC first-time experience is a focused wizard driven only by backend-required steps; completed users see a verification overview instead.
- OTP must be challenge-bound, single-use, correctly announced, and friendly to numeric mobile keyboards without exposing demo codes in production.
