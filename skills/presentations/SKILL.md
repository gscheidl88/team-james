---
name: presentations
description: "Create professional slide decks from Markdown using Marp — HTML, PDF, and PPTX export with version-controlled source"
agent: Researcher
tools_required: [node, npx, marp-cli]
wiki_ref: "[[marp]]"
version: "1.0"
---

# Skill: Presentations with Marp

**Category:** Communication & Reporting  
**Trigger:** Any task that produces a slide deck, status report, analysis presentation, or client-facing slides  
**Owner:** Researcher Agent (can be invoked by Analyst or James)

---

## When to Use This Skill

- Gerhard needs a slide deck for a project status update, sprint review, or client meeting
- An analysis result needs to be presented (not just documented)
- A wiki page or report should be exported as a shareable PDF/PPTX
- Technical architecture decisions need to be communicated visually
- Any "put this into a presentation" request

---

## Standard Workflow

```
1. PLAN      → Identify audience, key message, slide count (~10-15 slides)
2. STRUCTURE → Title / Agenda / Context / Findings / Recommendations / Next Steps
3. WRITE     → Author .md file with Marp front-matter (marp: true)
4. PREVIEW   → VS Code live preview OR: marp -w deck.md
5. EXPORT    → npx marp --pdf --allow-local-files deck.md
6. REVIEW    → Check pagination, font sizes, image quality
7. DELIVER   → Share PDF / PPTX or serve HTML locally
```

---

## Safe-layout and readability rules

- Reserve explicit space for Marp headers, footers, and page numbers — do not fill content all the way to the slide edge.
- If a slide feels "just barely fitting", split it. Dense finance and comparison slides should favor **more slides** over microscopic text.
- Use `<!-- _class: compact -->` for moderately dense slides and `<!-- _class: dense -->` only as an exception.
- Avoid dark-background summary slides unless contrast is checked explicitly.
- For final/disclaimer slides, prefer light backgrounds with dark text unless there is a strong reason not to.

### Footer-overlap prevention checklist

1. Keep long tables to roughly 6-8 rows on normal slides.
2. Avoid stacking a large table and a large callout box on the same slide.
3. On dense slides, shorten prose before shrinking type.
4. Re-export to PDF and visually inspect the footer area before delivery.

### Contrast check workflow

Use the local contrast checker before finalizing custom colors or dark slides:

```powershell
uv run tools/presentations/contrast_check.py --fg FFFFFF --bg 003366
uv run tools/presentations/contrast_check.py --fg 1A1A2E --bg F5F7FA
```

Interpretation:

- **PASS** = safe for the selected WCAG threshold
- **FAIL** = use the suggested simple text color or choose a different background

---

## Minimal Marp Front-matter

```markdown
---
marp: true
theme: default
size: 16:9
paginate: true
header: "Project Name · 2026"
footer: "Confidential"
---
```

---

## Key Marp Syntax Reference

### Slide separator

```markdown
# Slide 1

Content here.

---

# Slide 2

Content here.
```

### Themes

```yaml
theme: default    # Clean white — good for internal docs
theme: gaia       # Color accent header — good for client decks
theme: uncover    # Minimal, centered — good for title-heavy decks
```

### Title slide (centered layout)

```markdown
---
marp: true
theme: gaia
---

<!-- _class: lead -->

# Project Alpha — Q3 Status Report

**Analyst:** Gerhard's Team  
**Date:** 2026-04-10
```

### Per-slide color override (spot directive)

```markdown
<!-- _backgroundColor: #003366 -->
<!-- _color: white -->

## Section Divider

### Phase 2: Analysis
```

### Background image

```markdown
![bg cover](./assets/banner.jpg)

## Slide with full background image
```

### Background left (split layout — image + text)

```markdown
![bg left 40%](./assets/chart.png)

## Chart Interpretation

- Revenue grew 18% YoY
- Top 3 categories account for 72% of total
- Margin improved by 2.1 pp
```

### Image filter effects (brightness, blur, grayscale)

```markdown
<!-- Darken image for text overlay — essential for quote slides -->
![bg brightness:0.2](./assets/hero.jpg)

# Quote or headline in white

---

<!-- Ghost background — keeps table/text readable, adds visual interest -->
![bg opacity:0.08](./assets/watermark-logo.png)

## Slide with subtle background

---

<!-- Blur + dim — atmospheric background -->
![bg blur:4px brightness:0.6](./assets/office.jpg)

## Section intro text

---

<!-- Multiple filters combined -->
![bg brightness:1.2 contrast:1.1](./assets/chart.png)
```

### Sized inline image (not background)

```markdown
## Architecture Diagram

![w:700px](./assets/architecture.png)

*Figure 1: System components and data flow*

---

<!-- Two-size comparison -->
![w:380px](./assets/before.png)  ![w:380px](./assets/after.png)
```

### Before/After split layout

```markdown
![bg left:50%](./assets/before.png)
![bg right:50%](./assets/after.png)
```

### Vertical image comparison

```markdown
![bg vertical](./assets/top.png)
![bg](./assets/bottom.png)
```

### 3-split image grid

```markdown
![bg](./assets/option-a.png)
![bg](./assets/option-b.png)
![bg](./assets/option-c.png)
```

### Two-column layout (CSS Grid)

```markdown
---
marp: true
style: |
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
---

<div class="cols">
<div>

**Strengths**
- Strong pipeline
- Low churn

</div>
<div>

**Risks**
- Supply chain delays
- Key person dependency

</div>
</div>
```

### Inline style override

```yaml
---
style: |
  section { font-size: 26px; }
  h1 { color: #003366; border-bottom: 2px solid #ffcc00; }
  table { font-size: 20px; }
---
```

### Presenter notes

```markdown
# Slide Title

Content visible to audience.

<!-- Speaker: Mention the Q3 numbers. Pause for questions after this slide. -->
```

### Math (MathJax)

```markdown
---
math: mathjax
---

Revenue growth formula: $g = \frac{R_t - R_{t-1}}{R_{t-1}} \times 100$
```

---

## CLI Export Commands

```powershell
# Quick HTML preview (no browser needed)
npx @marp-team/marp-cli@latest deck.md

# PDF (requires Chrome/Edge)
npx @marp-team/marp-cli@latest --pdf --allow-local-files deck.md

# PPTX
npx @marp-team/marp-cli@latest --pptx --allow-local-files deck.md

# Watch mode during authoring
npx @marp-team/marp-cli@latest -w deck.md

# Custom theme
npx @marp-team/marp-cli@latest --theme ./themes/corp.css --pdf deck.md

# All images (one PNG per slide)
npx @marp-team/marp-cli@latest --images png deck.md
```

---

## Complete Working Example

Save as `project-status.md` — a real analyst-style "Project Status Report":

```markdown
---
marp: true
theme: default
size: 16:9
paginate: true
header: "Project Alpha · Q2 2026 Status Report"
footer: "Gerhard's Team — Internal Use Only"
style: |
  section {
    font-family: "Calibri", "Segoe UI", sans-serif;
    font-size: 26px;
  }
  h1 { color: #003366; border-bottom: 2px solid #0066cc; padding-bottom: 8px; }
  h2 { color: #0066cc; }
  table { font-size: 20px; width: 100%; }
  th { background-color: #003366; color: white; }
  .highlight { background-color: #fff3cd; padding: 12px; border-left: 4px solid #ffcc00; }
---

<!-- _class: lead -->
<!-- _paginate: skip -->

# Project Alpha
## Q2 2026 Status Report

**Prepared by:** Analyst Agent  
**Date:** 2026-04-10  
**Status:** 🟢 On Track

---

## Agenda

1. Executive Summary
2. KPI Dashboard
3. Key Achievements
4. Risks & Issues
5. Next Steps

---

## Executive Summary

<div class="highlight">

**Overall Status: 🟢 On Track** — Project Alpha is progressing within budget and on schedule. Revenue target 78% achieved with 6 weeks remaining in Q2.

</div>

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Revenue | €1.5M | €1.17M (78%) | 🟡 Watch |
| Margin | 32% | 34.2% | 🟢 Ahead |
| Delivery | Week 26 | Week 25 (est.) | 🟢 Ahead |
| Budget | €420k | €398k (95%) | 🟢 On Track |

---

## KPI Dashboard

![bg right 55%](./assets/kpi-chart.png)

### Revenue by Category

| Category | Q2 Target | Q2 Actual | Δ |
|----------|-----------|-----------|---|
| Product A | €600k | €512k | -15% |
| Product B | €550k | €481k | -13% |
| Services | €350k | €177k | -49% |

> ⚠️ Services lag is the primary watch item — pipeline review scheduled for Week 17.

---

## Key Achievements

- ✅ Phase 1 delivery completed 1 week ahead of schedule
- ✅ Customer satisfaction score: **4.6 / 5.0** (target: 4.0)
- ✅ 3 new enterprise accounts signed in April
- ✅ Infrastructure migration completed — cost saving: **€12k/month**
- ✅ Team reached full capacity (last 2 hires onboarded)

---

<!-- _class: invert -->

## Risks & Issues

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|-----------|------------|
| R1 | Services pipeline delay | High | Medium | Weekly pipeline review; fallback: upsell existing accounts |
| R2 | Key person unavailable (CTO) | High | Low | Knowledge transfer documented in wiki |
| R3 | Competitor price pressure | Medium | Medium | Value-based positioning reviewed with Sales |

---

## Next Steps

### Week 17–18

1. **Services pipeline review** — Sales + Delivery joint session
2. **Q3 forecast submission** — Analyst Agent prepares model by April 18
3. **Phase 2 kickoff** — Scope sign-off with stakeholders
4. **Hiring** — 2 open roles: Backend Engineer, Data Analyst

### Decision needed by EOW

> Approve Q3 budget extension of **€35k** for infrastructure scale-up (ROI: 3.2× by Q4).

---

<!-- _class: lead -->
<!-- _paginate: skip -->

# Questions?

**Contact:** Gerhard's Team  
**Deck source:** `plans/project-alpha-q2-status.md`  
**Next review:** 2026-05-08
```

Export this deck:

```powershell
npx @marp-team/marp-cli@latest --pdf --allow-local-files project-status.md -o "Project Alpha Q2 2026.pdf"
```

---

## Output Checklist

- [ ] `marp: true` in front-matter
- [ ] Theme and size declared
- [ ] Header and footer set (date + project name)
- [ ] Title slide uses `<!-- _class: lead -->` and `<!-- _paginate: skip -->`
- [ ] Paginate enabled from slide 2 onwards
- [ ] Tables have consistent column widths
- [ ] Images referenced with relative paths (use `--allow-local-files` for PDF)
- [ ] Presenter notes added to complex slides
- [ ] Exported PDF opens correctly in browser / Acrobat
- [ ] Source `.md` committed to Git

---

## McKinsey-Style Deck Patterns

> For full examples and CSS code, see [[marp-advanced]] and `corp-theme.css`.

### Action Title Rule

Every slide title **is** the key message — a complete sentence, not a topic label.

```
❌ "Revenue Overview"
✅ "Revenue grew 18% YoY — all three segments exceeded target"
```

Read only the titles in sequence: the audience should follow the full story without reading slide bodies.

### SCQA Structure for Full Deck

Map the Barbara Minto SCQA framework to your slide sequence:

```
Slide 1 — Title slide
Slide 2 — Situation: "This is the context"
Slide 3 — Complication: "This is the problem / tension"
Slide 4 — Question: "What should we do?"
Slide 5 — Answer: "Here is the recommendation"
Slides 6–N — Evidence and support
Last slide — Decisions required / Next steps
```

Apply via `<!-- _class: divider -->` to separate SCQA phases as named sections.

### KPI Block Pattern (with `corp-theme.css`)

Use `.kpi-grid` + `.kpi-card` from `corp-theme.css` for the KPI dashboard slide:

```markdown
---
marp: true
theme: corp
size: 16:9
paginate: true
---

## Four KPIs confirm the positive trajectory

<div class="kpi-grid">

<div class="kpi-card">
<div class="kpi-number">€ 2.3M</div>
<div class="kpi-label">Revenue</div>
<div class="kpi-delta kpi-up">▲ 18%</div>
</div>

<div class="kpi-card">
<div class="kpi-number">34.2%</div>
<div class="kpi-label">Gross Margin</div>
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

**Traffic light variant:** Replace `.kpi-number` with `🟢 / 🟡 / 🔴` emoji (font-size: 48px inline style).

### Image + Split Layout Pattern

Use Marp's native `![bg left 40%]` directive for image+text splits — no CSS needed:

```markdown
![bg left 40%](https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800)

## Revenue growth accelerated — three consecutive quarters of outperformance

- Core product: +24% YoY (enterprise segment expansion)
- Services: pipeline fully rebuilt after Q2 dip
- DACH now 38% of revenue (up from 29%)

> Source: Internal CRM, confirmed Finance — September 2026
```

For external images in PDF export: use stable CDN URLs (Unsplash, Wikimedia Commons).  
Always add a small attribution caption (`.photo-caption` class from `corp-theme.css`).

### Corp Theme Quick-Start

```powershell
# Register corp-theme for CLI builds
npx @marp-team/marp-cli@latest --theme ./skills/presentations/corp-theme.css --pdf deck.md
```

```json
// .vscode/settings.json — register for VS Code live preview
{
  "markdown.marp.themes": ["./skills/presentations/corp-theme.css"]
}
```

Front-matter:
```yaml
---
marp: true
theme: corp
size: 16:9
paginate: true
header: "Project Name · Month Year"
footer: "Confidential — Internal Use Only"
---
```

### McKinsey Deck Quality Gate

Before delivering any deck, verify:

- [ ] Every title passes the "So What?" test (key message, not topic label)
- [ ] Deck follows SCQA arc in first 5 slides
- [ ] KPI dashboard slide present with big-number cards
- [ ] Max 5 bullets per slide (aim for 3) — **1 slide = 1 message**
- [ ] Consistent color usage (only corp-theme palette)
- [ ] All data points have source attribution
- [ ] Footer shows confidentiality level on every content slide
- [ ] Slide count appropriate: 5 min → 5-8 slides; 10 min → 10-15; 20 min → 15-25
- [ ] Every section break slide (divider) has a subtitle below the heading
- [ ] Images have clear purpose (aid understanding, not decoration)
- [ ] Quote slides have a background image at `brightness:0.2` for impact

---

## Theme Selection Guide

| Audience/Context | Recommended Theme | Note |
|-----------------|-------------------|------|
| Executive / Client / McKinsey-style | `corp` | KPI-cards, SCQA, action titles |
| General seminar / internal | `gaia` or `default` | Clean, fast to author |
| Youth / School / Creative | Colorful CSS (inline) | Pink gradient, rainbow h2::after |
| Tech / Dev talk | `uncover` or dark CSS | Minimal or GitHub-dark |
| Academic / content-heavy | `default` | Wide margins, light fonts |

**For youth/school content**, add this CSS to inline `style:` block:

```css
/* Youth-friendly overlay — adds energy to gaia/default theme */
section.lead h1 {
  background: linear-gradient(135deg, #8B4A8B, #C27BC2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
h2::after {
  content: '';
  display: block;
  width: 60px; height: 3px;
  background: linear-gradient(90deg, #C9923A, #8B4A8B, #4d96ff);
  border-radius: 2px;
  margin-top: 4px;
}
ul li::marker { color: #8B4A8B; font-weight: bold; }
```
