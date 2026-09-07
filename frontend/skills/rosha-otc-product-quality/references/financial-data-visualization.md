# Financial data-visualization pass

- Charts must encode actual service data; development mock mode may supply a realistic deterministic time series.
- Prefer the existing chart solution. Introduce at most one maintained primary chart system when the current implementation cannot meet interaction/accessibility needs.
- Provide responsive resize, high-DPI rendering, dark-theme contrast, reduced motion, touch interaction, loading, empty, and error states.
- Portfolio charts expose meaningful ranges such as ۷ روز، ۳۰ روز، ۹۰ روز when backed by data.
- Use a restrained area gradient, a clear line, minimal grid/axes, and no decorative fake trend.
- Format Persian tooltip date and amount; keep the numeric value readable with an explicit Toman or asset unit.
- Sparklines are optional scanning aids for market/asset lists, not decoration. Provide a textual trend/value equivalent for assistive technology.
- Mobile charts reduce axis density and height while retaining an adequately sized touch target.
