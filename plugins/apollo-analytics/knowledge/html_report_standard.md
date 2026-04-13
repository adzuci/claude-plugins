# Jarvis HTML Report Standard

All Jarvis report outputs default to self-contained dark-mode HTML. This file defines the shared styling and structure that every skill and suit must follow.

## When to use HTML vs Markdown

| Output type | Format |
|---|---|
| Single number, quick answer, conversational | Markdown |
| Multi-section report, debrief, deep dive, trend analysis | HTML |
| Weekly insights, account profile, credit analysis | HTML |
| Error message, clarifying question | Markdown |

**Default is HTML.** Only fall back to markdown for quick answers.

## CSS Variables (mandatory for all HTML reports)

```css
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface-hover: #232736;
  --border: #2d3148;
  --text: #e4e4e7;
  --muted: #9ca3af;
  --accent: #6c63ff;
  --accent-soft: rgba(108, 99, 255, 0.15);
  --teal: #00d4aa;
  --teal-soft: rgba(0, 212, 170, 0.15);
  --red: #ff6b6b;
  --red-soft: rgba(255, 107, 107, 0.15);
  --yellow: #ffd166;
  --yellow-soft: rgba(255, 209, 102, 0.15);
}
```

## Fonts

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  color: var(--text);
  background: var(--bg);
}
code, .mono {
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
```

No Google Fonts. All system fonts for zero external dependencies.

## Report Structure

Every HTML report follows this layout:

```
┌─────────────────────────────────────────────┐
│  Header: Title + Subtitle + Date            │
├─────────────────────────────────────────────┤
│  Verdict Section (always visible)           │
│  - One-sentence conclusion                  │
│  - Status indicators: ✅ ⚠️ 🔴              │
├─────────────────────────────────────────────┤
│  KPI Cards Row                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│  │ KPI1 │ │ KPI2 │ │ KPI3 │ │ KPI4 │      │
│  └──────┘ └──────┘ └──────┘ └──────┘      │
├─────────────────────────────────────────────┤
│  Tab Navigation (for multi-section)         │
│  [Tab 1] [Tab 2] [Tab 3] [Methodology]     │
├─────────────────────────────────────────────┤
│  Tab Content                                │
│  - Charts (Chart.js)                        │
│  - Data tables                              │
│  - Narrative sections                       │
├─────────────────────────────────────────────┤
│  Footer: "Jarvis for [user]" + timestamp    │
└─────────────────────────────────────────────┘
```

## KPI Card HTML

```html
<div class="kpi-card">
  <div class="kpi-label">Metric Name</div>
  <div class="kpi-value">$199M</div>
  <div class="kpi-delta positive">+3.2% vs prior</div>
</div>
```

```css
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.kpi-label { color: var(--muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-value { font-size: 2rem; font-weight: 700; margin: 8px 0; }
.kpi-delta.positive { color: var(--teal); }
.kpi-delta.negative { color: var(--red); }
.kpi-delta.neutral { color: var(--yellow); }
```

## Verdict Status Badges

```html
<span class="badge badge-green">✅ On Track</span>
<span class="badge badge-yellow">⚠️ Watch</span>
<span class="badge badge-red">🔴 At Risk</span>
```

## Chart.js Usage

- Use Chart.js via CDN: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- Dark theme: set `Chart.defaults.color = '#9ca3af'` and grid colors to `var(--border)`
- Accent color palette: `['#6c63ff', '#00d4aa', '#ff6b6b', '#ffd166', '#a78bfa', '#60a5fa']`
- All charts must have visible axis labels and a legend

## Data Tables

```css
table { width: 100%; border-collapse: collapse; }
th { background: var(--surface); color: var(--muted); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; padding: 12px; text-align: left; }
td { padding: 12px; border-bottom: 1px solid var(--border); }
tr:hover { background: var(--surface-hover); }
```

## File Naming

Save HTML reports to `/tmp/` with format: `<topic>_<date>.html`
- Example: `/tmp/ai_assistant_debrief_2026_04_10.html`
- Example: `/tmp/credit_analysis_mid_market_2026_04_10.html`

## Sharing

After generating an HTML report, use the `share-report` skill to upload to GCS and get a shareable URL.
