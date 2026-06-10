# Visual System

Use a professional technical dashboard style: dense, sharp, and readable. Avoid marketing layout, decorative blobs, and purely illustrative visuals.

## Layout

- Make the first viewport the dashboard itself, not a landing page.
- Use a compact framed header with a source-aware subtitle, date-range pill, source chips, and Daily/Weekly/Monthly controls.
- Use compact KPI blocks, dense charts, source chips, and tables designed for repeated scanning.
- Keep cards to individual panels only. Do not nest cards inside cards.
- Keep border radius at 8px or less unless matching an existing local design system.
- Use stable dimensions for KPI rows, charts, toggles, and tables so data updates do not shift the layout.
- Avoid horizontal scrolling at mobile and desktop widths.

## Data Displays

- Default selected view should be the previous calendar month bounded by available measured data; expose actual discovered data bounds separately.
- Daily view should render as a regular Sunday-to-Saturday calendar grid, including weekday headers and leading/trailing empty days.
- Daily cells should include day numbers, intensity, and hover text with the full US-formatted date plus token/run details.
- Driver bars should show percentage share of measured burn.
- Source comparisons should make Codex, Claude, Antigravity, or other measured sources visually distinct instead of relying on a blended total alone.
- Breakdown tables should include source-specific token columns when multiple measured sources are present.
- Count labels should say `Runs` when they include subagents or other local run files; avoid labeling that number `Sessions`.
- Include a low-to-peak legend for heatmaps or intensity grids.
- Show the actual discovered date range.
- Show selectable dates with one clear control surface: visible month/range buttons for common ranges plus explicit US-format (`MM/DD/YYYY`) `From`/`To` text fields. Do not rely on dropdown-only selectors or duplicate native date inputs that can render in a different locale order from the US text fields.
- Show confidence labels where needed.
- Keep top KPIs and measured dashboard sections limited to exact or measured rows.
- Do not show not connected or estimated chat sources as if they were measured.

## Palette

- Base: OLED black or near-black surfaces, with restrained separation between page, panels, and rows.
- Text: high-contrast primary text, muted secondary text, and clear disabled states.
- Data colors: use multiple distinct hues for source and category comparison.
- Alerts: reserve warm colors for risk, missing data, or anomalous burn patterns.

## Interaction

- Daily, Weekly, and Monthly controls must update visible counts, labels, charts, and tables.
- Use keyboard-focusable controls with visible focus states.
- Keep animation restrained and avoid motion that hides data changes.

## Typography

- Use compact, legible type sized for dashboards.
- Do not scale font size with viewport width.
- Use letter spacing of `0`.
- Make long labels wrap cleanly or truncate with accessible full text.
