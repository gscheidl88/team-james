---
# ── Identity ──────────────────────────────────────────────
id: marp-advanced
type: documentation
title: "Marp Advanced — McKinsey/BCG Design Patterns"
tags: [marp, presentations, design, mckinsey, bcg, css, kpi, layout]
domain: technical

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-11
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by:
review_date:

# ── Provenance ────────────────────────────────────────────
created: 2026-04-11
created_by: Researcher
last_modified: 2026-04-11
modified_by: Researcher
source: https://marp.app/
ingest_session: [[log#2026-04-11-documentation-marp-advanced]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[marp]]"
depends_on:
  - "[[marp]]"
---

## Overview

This page documents advanced Marp presentation design patterns modeled on McKinsey/BCG consultant-grade slide standards. It covers six domains: the McKinsey Pyramid Principle applied to Marp slide structure; CSS patterns for KPI metric cards and big-number displays; professional color palettes and typography; image best practices using external URLs and split layouts; advanced multi-column and table layout patterns via CSS Grid; and a complete production-ready corporate CSS theme (`corp-theme.css`) ready for `/* @theme corp */` registration. All code examples are validated for Marp's `<section>`-based HTML rendering engine and work in both VS Code live preview and `marp --pdf` export.

---

## 1. McKinsey Slide Structure

### 1.1 Action Title (Headline-First) Pattern

Every slide title **is** the key message — not a topic label.

| ❌ Topic Label | ✅ Action Title (McKinsey) |
|---|---|
| "Revenue Overview" | "Revenue grew 18% YoY, ahead of target" |
| "Risk Analysis" | "Supply chain risk is the primary threat to Q3 delivery" |
| "Next Steps" | "Three decisions required by EOW to stay on track" |

**Rule:** Read only the titles of your deck in sequence. A listener should understand the full story without reading the content.

```markdown
<!-- _class: lead -->

# Revenue grew 18% YoY — all three segments above target
```

### 1.2 SCQA Framework for Full Deck Structure

The **Situation → Complication → Question → Answer** (Barbara Minto / McKinsey) structure maps directly to a Marp deck:

```
Slide 1 (Title):     Project Alpha — Q3 Performance Review
Slide 2 (Situation): "Alpha is our largest revenue contributor — €4.2M YTD"
Slide 3 (Complication): "Services segment fell 22% in Q3, threatening annual target"
Slide 4 (Question):  "Can we recover Q3 shortfall without extending budget?"
Slide 5 (Answer):    "Yes — three targeted actions close the gap with €0 additional spend"
Slides 6–9 (Support): Evidence, analysis, data
Slide 10 (Actions):  "Three decisions needed from leadership today"
```

**Marp front-matter SCQA template:**

```markdown
---
marp: true
theme: corp
size: 16:9
paginate: true
header: "Project Alpha · Q3 2026"
footer: "Confidential — Internal Use Only"
headingDivider: false
---

<!-- _class: lead -->
<!-- _paginate: skip -->

# Project Alpha
## Q3 Performance Review

**Prepared by:** the owner's Team | **Date:** 2026-09-30

---

<!-- _class: divider -->

# Situation

---

## Alpha is our largest contributor — €4.2M YTD, 43% of portfolio

...

---

<!-- _class: divider -->

# Complication

---

## Services fell 22% in Q3, putting annual target at risk

...
```

### 1.3 Pyramid Principle: Conclusion First

Place the key insight in the **title** (top of pyramid). Supporting evidence follows in the content area. Never bury the conclusion at the end of a slide.

```
TITLE (top):    "Cost reduction of €380k is achievable in 90 days"
CONTENT (body): Three initiatives → supporting data → assumptions
FOOTER:         Source / Confidentiality
```

### 1.4 "So What?" Test

Before finalizing each slide, ask: *"So what? Why does the audience care?"*  
If the answer is not in the title, rewrite the title.

```markdown
# Bad:  "Market Share Data"
# Good: "We hold #2 position with 18% share — gap to leader narrowed by 3pp this quarter"
```

### 1.5 Executive Summary — 3-Box Pattern

A standard McKinsey Exec Summary slide uses three boxes: Situation / Implication / Recommendation.

```markdown
---
style: |
  .exec-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
    margin-top: 1rem;
  }
  .exec-box {
    border: 2px solid #003366;
    border-radius: 6px;
    padding: 1.2rem;
    background: #f7f9fc;
  }
  .exec-box h3 {
    color: #003366;
    font-size: 16px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.6rem;
    border-bottom: 2px solid #0066cc;
    padding-bottom: 0.4rem;
  }
  .exec-box p { font-size: 18px; color: #1a1a2e; margin: 0; }
---

## Three actions close the Q3 gap without additional budget

<div class="exec-summary">
<div class="exec-box">
<h3>Situation</h3>
<p>Services segment €420k below target. Pipeline covers only 60% of shortfall.</p>
</div>
<div class="exec-box">
<h3>Implication</h3>
<p>Without action, annual revenue misses target by €180k (−4.3%). Margin impact: −1.8pp.</p>
</div>
<div class="exec-box">
<h3>Recommendation</h3>
<p>Activate three enterprise upsell plays immediately. Close gap by Nov 30 with existing team.</p>
</div>
</div>
```

---

## 2. KPI Metric Blocks / Big Number Cards

### 2.1 Single KPI Card Pattern

```html
<div class="kpi-card">
  <div class="kpi-number">€ 2.3M</div>
  <div class="kpi-label">Q3 Revenue</div>
  <div class="kpi-delta kpi-up">▲ 18% vs Q2</div>
</div>
```

Required CSS (include in `style:` block or use `corp-theme.css`):

```css
.kpi-card {
  border: 1.5px solid #d0d8e8;
  border-radius: 8px;
  padding: 1.4rem 1.6rem;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0,51,102,0.08);
  text-align: center;
}
.kpi-number {
  font-size: 64px;
  font-weight: 700;
  color: #0055a5;
  line-height: 1;
  margin-bottom: 0.3rem;
}
.kpi-label {
  font-size: 16px;
  color: #5a6a7a;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 500;
}
.kpi-delta {
  font-size: 18px;
  font-weight: 600;
  margin-top: 0.5rem;
}
.kpi-up   { color: #1a7c3e; }
.kpi-down { color: #b31b1b; }
.kpi-flat { color: #777777; }
```

### 2.2 Four KPI Cards in a Row

```markdown
---
style: |
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.2rem;
    margin-top: 1rem;
  }
  /* ... (kpi-card styles from above) ... */
---

## Q3 KPIs — All Core Metrics on Track

<div class="kpi-grid">

<div class="kpi-card">
<div class="kpi-number">€ 2.3M</div>
<div class="kpi-label">Revenue</div>
<div class="kpi-delta kpi-up">▲ 18%</div>
</div>

<div class="kpi-card">
<div class="kpi-number">34.2%</div>
<div class="kpi-label">Margin</div>
<div class="kpi-delta kpi-up">▲ 2.1pp</div>
</div>

<div class="kpi-card">
<div class="kpi-number">4.6</div>
<div class="kpi-label">CSAT Score</div>
<div class="kpi-delta kpi-flat">→ Stable</div>
</div>

<div class="kpi-card">
<div class="kpi-number">97%</div>
<div class="kpi-label">On-Time Delivery</div>
<div class="kpi-delta kpi-down">▼ −1pp</div>
</div>

</div>
```

### 2.3 Traffic Light Status Cards

```markdown
<div class="kpi-grid">

<div class="kpi-card">
<div style="font-size:48px">🟢</div>
<div class="kpi-label">Delivery</div>
<div style="font-size:18px; color:#1a7c3e; font-weight:600">On Track</div>
</div>

<div class="kpi-card">
<div style="font-size:48px">🟡</div>
<div class="kpi-label">Revenue</div>
<div style="font-size:18px; color:#b36000; font-weight:600">Watch</div>
</div>

<div class="kpi-card">
<div style="font-size:48px">🔴</div>
<div class="kpi-label">Services Pipeline</div>
<div style="font-size:18px; color:#b31b1b; font-weight:600">At Risk</div>
</div>

<div class="kpi-card">
<div style="font-size:48px">🟢</div>
<div class="kpi-label">Budget</div>
<div style="font-size:18px; color:#1a7c3e; font-weight:600">Under Budget</div>
</div>

</div>
```

---

## 3. Professional Color & Typography

### 3.1 McKinsey Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Primary Navy | Dark corporate blue | `#003366` |
| Primary Blue | Hyperlink / accent | `#0055a5` |
| Light Blue | Secondary accent | `#0099cc` |
| Charcoal | Body text | `#1a1a2e` |
| Medium Gray | Secondary text | `#5a6a7a` |
| Light Gray | Borders, alternating rows | `#e8edf3` |
| Warm White | Slide background | `#fafbfd` |
| Yellow Accent | Callouts, highlights | `#f5a623` |
| Success Green | Positive deltas | `#1a7c3e` |
| Alert Red | Negative deltas, risks | `#b31b1b` |

### 3.2 BCG Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Primary Green | BCG brand | `#1a6e4b` |
| Dark Green | Headings | `#0d4030` |
| Light Green | Accents | `#3ab07a` |
| Charcoal | Body text | `#2c2c2c` |
| Gray | Secondary | `#6b7280` |
| Slate White | Background | `#f9fafb` |

### 3.3 Professional Font Stack (Windows)

```css
section {
  /* Primary: Microsoft Office fonts (installed on all Windows) */
  font-family: "Calibri", "Segoe UI", "Arial", sans-serif;

  /* Alternative: Google Fonts (requires internet + @import) */
  /* font-family: "Inter", "Roboto", sans-serif; */

  font-size: 26px;
  line-height: 1.5;
}

h1, h2, h3 {
  font-family: "Calibri", "Segoe UI", sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
}
```

**Recommended font sizes for 16:9 (1280×720):**

| Element | Font Size |
|---------|-----------|
| Slide title (h1) | 40–48px |
| Section heading (h2) | 32–36px |
| Body text | 24–28px |
| Table / footnote | 18–20px |
| KPI number | 56–72px |
| Footer | 14px |

### 3.4 Slide Size: 16:9 vs 4:3

```yaml
size: 16:9   # 1280×720px — screens, web, video, modern projectors → default
size: 4:3    # 960×720px  — legacy projectors, A4 printing, classic decks
```

**Rule:** Use `16:9` always unless you know the output is A4 paper or a legacy projector.

### 3.5 White Space First Principle

- Minimum 10% margin on all sides (Marp default theme provides this)
- Maximum 5 bullet points per slide — prefer 3
- Single chart per slide; never crowd two charts side by side
- Content area: max 70% of slide height (leave room for titles + footer)
- KPI grid: max 4 cards per row; 3 preferred

---

## 4. Image Best Practices in Marp

### 4.1 External URLs in `![bg]` (No Local Files Needed)

```markdown
<!-- Wikimedia Commons — free, stable URLs -->
![bg cover](https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/24701-nature-natural-beauty.jpg/1280px-24701-nature-natural-beauty.jpg)

<!-- Unsplash (free, high-res, no attribution required for slides) -->
![bg cover](https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1280)

<!-- Picsum (placeholder images for prototyping) -->
![bg cover](https://picsum.photos/1280/720?grayscale)
```

> **Note:** External URLs work in HTML export. For PDF export, Marp fetches them during render — stable CDN URLs are reliable. Test with `marp --pdf` before delivery.

### 4.2 Split Layout: Image Left + Text Right

```markdown
![bg left 40%](https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800)

## Revenue growth accelerated in Q3 — highest since 2022

- Core product: +24% YoY growth driven by enterprise expansion
- Services: recovery underway — pipeline now fully rebuilt
- Geographic mix shift: DACH region now 38% of total (was 29%)

> Source: Internal CRM data, confirmed by Finance — September 2026
```

### 4.3 Photo + Caption + Source Attribution

```markdown
---
style: |
  .photo-caption {
    position: absolute;
    bottom: 60px;
    right: 20px;
    font-size: 12px;
    color: rgba(255,255,255,0.75);
    text-align: right;
    max-width: 300px;
  }
---

![bg cover](https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1280)

<!-- _color: white -->

# Market expansion is the defining growth lever for 2027

<div class="photo-caption">
Photo: Unsplash / Carlos Muza<br>
Free to use under Unsplash License
</div>
```

### 4.4 Overlay Text Readability

For text over images, always add a dark overlay or use the Marp `color` directive:

```markdown
---
style: |
  section.bg-overlay::before {
    content: "";
    position: absolute;
    inset: 0;
    background: rgba(0, 20, 51, 0.62);
    z-index: 0;
  }
  section.bg-overlay * {
    position: relative;
    z-index: 1;
  }
---

<!-- _class: bg-overlay -->

![bg cover](https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1280)

# Three strategic priorities define our 2027 roadmap

- International expansion (€600k investment, €2.1M projected return)
- Platform modernization (completed Q1 2027)
- Enterprise sales motion (new VP hired, target: 5 enterprise accounts)
```

### 4.5 Image Licensing Attribution

| Source | License | Attribution Required |
|--------|---------|---------------------|
| Unsplash | Unsplash License | Not required (good practice) |
| Wikimedia Commons | CC BY / CC0 / GFDL | Required for CC BY (caption) |
| Pexels | Pexels License | Not required |
| Pixabay | Pixabay License | Not required |
| Getty / Shutterstock | Commercial | License required — avoid in internal decks |

**Best practice:** Add a small caption div with source even when not legally required — it signals diligence.

---

## 5. Advanced Layout Patterns

### 5.1 Three-Column Layout (CSS Grid)

```markdown
---
style: |
  .columns-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.8rem;
    margin-top: 1rem;
  }
  .col-card {
    padding: 1rem;
    border-left: 4px solid #0055a5;
    background: #f7f9fc;
  }
  .col-card h3 {
    color: #003366;
    font-size: 20px;
    margin-bottom: 0.5rem;
  }
---

## Three strategic levers drive the recovery plan

<div class="columns-3">
<div class="col-card">
<h3>🎯 Revenue</h3>

Activate 6 enterprise upsell plays.  
Target: €280k additional Q4 revenue.  
Owner: Sales (VP Carlos)

</div>
<div class="col-card">
<h3>⚙️ Operations</h3>

Reduce delivery lead time by 30%.  
Automation sprint: 3 workflows.  
Owner: Delivery (Lead Anna)

</div>
<div class="col-card">
<h3>💡 Product</h3>

Release Feature Pack 3.2.  
NPS improvement target: +12 pts.  
Owner: Product (PM Tobias)

</div>
</div>
```

### 5.2 Icon + Number + Label Card Grid (4 per slide)

```markdown
---
style: |
  .icon-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
    margin-top: 1.5rem;
  }
  .icon-card {
    text-align: center;
    padding: 1.5rem 1rem;
    border: 1px solid #d0d8e8;
    border-radius: 10px;
    background: #fafbfd;
  }
  .icon-card .icon   { font-size: 44px; margin-bottom: 0.4rem; }
  .icon-card .figure { font-size: 40px; font-weight: 700; color: #003366; line-height: 1.1; }
  .icon-card .metric { font-size: 15px; color: #5a6a7a; margin-top: 0.3rem; }
---

## Q3 impact — four headline numbers

<div class="icon-grid">

<div class="icon-card">
<div class="icon">🏆</div>
<div class="figure">€ 2.3M</div>
<div class="metric">Revenue achieved</div>
</div>

<div class="icon-card">
<div class="icon">📈</div>
<div class="figure">+18%</div>
<div class="metric">YoY growth rate</div>
</div>

<div class="icon-card">
<div class="icon">😊</div>
<div class="figure">4.6 / 5</div>
<div class="metric">Customer satisfaction</div>
</div>

<div class="icon-card">
<div class="icon">✅</div>
<div class="figure">97%</div>
<div class="metric">On-time delivery</div>
</div>

</div>
```

### 5.3 Quote Slide Pattern (Large Pull Quote)

```markdown
---
style: |
  .pull-quote {
    border-left: 6px solid #0055a5;
    padding: 1.5rem 2rem;
    margin: 2rem 0;
    background: #f0f5ff;
    border-radius: 0 8px 8px 0;
  }
  .pull-quote blockquote {
    font-size: 32px;
    font-style: italic;
    color: #1a1a2e;
    margin: 0 0 1rem 0;
    line-height: 1.4;
    border: none;
    padding: 0;
    background: transparent;
  }
  .pull-quote .attribution {
    font-size: 18px;
    color: #5a6a7a;
    font-weight: 600;
  }
---

## Customer voice confirms the strategic direction

<div class="pull-quote">
<blockquote>
"The turnaround in delivery performance over the last 90 days has been
remarkable. Alpha is now our most reliable vendor in this category."
</blockquote>
<div class="attribution">— Chief Procurement Officer, Enterprise Client (€480k ARR)</div>
</div>

> Internal CSAT survey, September 2026 — 94% response rate
```

### 5.4 Process Flow / Timeline (No Mermaid)

```markdown
---
style: |
  .timeline {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    margin-top: 1.5rem;
    position: relative;
  }
  .timeline::before {
    content: "";
    position: absolute;
    top: 28px;
    left: 10%;
    right: 10%;
    height: 3px;
    background: #0055a5;
    z-index: 0;
  }
  .tl-step {
    text-align: center;
    position: relative;
    z-index: 1;
    padding: 0 0.8rem;
  }
  .tl-dot {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: #0055a5;
    color: white;
    font-size: 22px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 0.8rem auto;
    box-shadow: 0 2px 8px rgba(0,85,165,0.3);
  }
  .tl-dot.done   { background: #1a7c3e; }
  .tl-dot.active { background: #0055a5; box-shadow: 0 0 0 4px rgba(0,85,165,0.2); }
  .tl-dot.future { background: #d0d8e8; color: #5a6a7a; }
  .tl-title  { font-size: 18px; font-weight: 700; color: #003366; margin-bottom: 0.3rem; }
  .tl-date   { font-size: 14px; color: #5a6a7a; margin-bottom: 0.3rem; }
  .tl-status { font-size: 13px; }
---

## Project Alpha — Four-phase delivery plan, Phase 2 active

<div class="timeline">

<div class="tl-step">
<div class="tl-dot done">✓</div>
<div class="tl-title">Phase 1</div>
<div class="tl-date">Jan–Mar 2026</div>
<div class="tl-status" style="color:#1a7c3e">✅ Complete</div>
</div>

<div class="tl-step">
<div class="tl-dot active">2</div>
<div class="tl-title">Phase 2</div>
<div class="tl-date">Apr–Jun 2026</div>
<div class="tl-status" style="color:#0055a5">🔵 In Progress</div>
</div>

<div class="tl-step">
<div class="tl-dot future">3</div>
<div class="tl-title">Phase 3</div>
<div class="tl-date">Jul–Sep 2026</div>
<div class="tl-status" style="color:#5a6a7a">⬜ Planned</div>
</div>

<div class="tl-step">
<div class="tl-dot future">4</div>
<div class="tl-title">Launch</div>
<div class="tl-date">Oct 2026</div>
<div class="tl-status" style="color:#5a6a7a">⬜ Planned</div>
</div>

</div>
```

### 5.5 Financial Data Table Styling

```markdown
---
style: |
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 20px;
    margin-top: 1rem;
  }
  th {
    background-color: #003366;
    color: white;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
  td {
    padding: 9px 14px;
    border-bottom: 1px solid #e8edf3;
    color: #1a1a2e;
  }
  tr:nth-child(even) td { background-color: #f2f5fa; }
  tr:last-child td {
    background-color: #e8f0fb;
    font-weight: 700;
    border-top: 2px solid #003366;
  }
  td:nth-child(n+2) { text-align: right; }
  th:nth-child(n+2) { text-align: right; }
---

## P&L Summary — Q3 2026 vs Budget

| Line Item | Budget | Actual | Δ Abs. | Δ % |
|---|---|---|---|---|
| Revenue | € 2,000k | € 2,280k | +€ 280k | +14.0% |
| Cost of Sales | € 1,200k | € 1,331k | +€ 131k | +10.9% |
| Gross Profit | € 800k | € 949k | +€ 149k | +18.6% |
| Operating Expenses | € 350k | € 342k | −€ 8k | −2.3% |
| **EBIT** | **€ 450k** | **€ 607k** | **+€ 157k** | **+34.9%** |
```

---

## 6. Corporate CSS Theme — Usage Guide

The full production theme is in `skills/presentations/corp-theme.css`.

### 6.1 Registration

**VS Code (`.vscode/settings.json`):**
```json
{
  "markdown.marp.themes": [
    "./skills/presentations/corp-theme.css"
  ]
}
```

**CLI:**
```powershell
npx @marp-team/marp-cli@latest --theme ./skills/presentations/corp-theme.css --pdf deck.md
```

**Front-matter:**
```yaml
---
marp: true
theme: corp
size: 16:9
paginate: true
---
```

### 6.2 Slide Class Reference

| Class | Usage | How to Apply |
|-------|-------|-------------|
| (none) | Standard content slide | Default — no class needed |
| `lead` | Title slide — dark navy bg, white, centered | `<!-- _class: lead -->` |
| `divider` | Section break — accent blue, centered | `<!-- _class: divider -->` |
| `invert` | Dark content slide | `<!-- _class: invert -->` |

### 6.3 CSS Component Classes

| Class | Use |
|-------|-----|
| `.kpi-grid` | CSS Grid wrapper for KPI cards (3–4 per row) |
| `.kpi-card` | Individual KPI block with border and shadow |
| `.kpi-number` | Big number display (64px, corporate blue) |
| `.kpi-label` | Small caption below the number |
| `.kpi-delta` + `.kpi-up` / `.kpi-down` | Trend indicator (green / red) |
| `.columns-2` | 50/50 two-column grid |
| `.columns-3` | 33/33/33 three-column grid |
| `.columns-left` | 40/60 split (left-heavy) |
| `.exec-summary` + `.exec-box` | 3-box Situation/Implication/Recommendation grid |
| `.pull-quote` | Large italic blockquote with left border |
| `.timeline` + `.tl-step` + `.tl-dot` | 4-step process flow |
| `.icon-grid` + `.icon-card` | Icon + number + label cards |

### 6.4 Complete Minimal Deck Template

```markdown
---
marp: true
theme: corp
size: 16:9
paginate: true
header: "Project Name · Month Year"
footer: "Confidential — Internal Use Only"
---

<!-- _class: lead -->
<!-- _paginate: skip -->

# Project Name
## Deck Type — Month Year

**Prepared by:** the owner's Team

---

<!-- _class: divider -->

# Section 1: Situation

---

## Title is the key message — not a topic label

Content supports the title. Three bullets maximum.

- First supporting point with data
- Second supporting point
- Third supporting point (most important last)

---

<!-- _class: divider -->

# Section 2: Findings

---

## Four KPIs confirm the positive trajectory

<div class="kpi-grid">
<div class="kpi-card">
<div class="kpi-number">€ 2.3M</div>
<div class="kpi-label">Revenue</div>
<div class="kpi-delta kpi-up">▲ 18%</div>
</div>
<div class="kpi-card">
<div class="kpi-number">34%</div>
<div class="kpi-label">Margin</div>
<div class="kpi-delta kpi-up">▲ 2pp</div>
</div>
<div class="kpi-card">
<div class="kpi-number">4.6</div>
<div class="kpi-label">CSAT</div>
<div class="kpi-delta kpi-flat">→ Stable</div>
</div>
<div class="kpi-card">
<div class="kpi-number">97%</div>
<div class="kpi-label">On-Time</div>
<div class="kpi-delta kpi-down">▼ −1pp</div>
</div>
</div>

---

<!-- _class: lead -->
<!-- _paginate: skip -->

# Questions?

**Contact:** the owner's Team
**Next review:** [Date]
```

---

## McKinsey Deck Quality Checklist

- [ ] **Action titles:** Every slide title is a full sentence stating the key message
- [ ] **SCQA arc:** Situation → Complication → Question → Answer visible across first 5 slides
- [ ] **3 bullets max:** No slide has more than 5 bullet points; aim for 3
- [ ] **One message per slide:** Remove slides that do not directly support the deck's main recommendation
- [ ] **KPI slide:** Dashboard slide with 3–4 big-number cards early in the deck
- [ ] **Executive Summary:** 3-box structure present on slide 2 or 3
- [ ] **White space:** Content uses < 70% of slide area; margins are generous
- [ ] **Consistent color:** Only McKinsey palette colors — no ad-hoc hex values
- [ ] **Footer:** Confidentiality level + slide number on every content slide
- [ ] **Source attribution:** All data points have a source (even if just "Internal data, Q3 2026")
