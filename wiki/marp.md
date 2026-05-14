---
# ── Identity ──────────────────────────────────────────────
id: marp
type: documentation
title: "Marp — Markdown Presentation Ecosystem"
tags: [marp, presentations, markdown, cli, vscode]
domain: technical

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-10
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by:
review_date:

# ── Provenance ────────────────────────────────────────────
created: 2026-04-10
created_by: Researcher
last_modified: 2026-04-10
modified_by: Researcher
source: https://marp.app/
ingest_session: [[log#2026-04-10-documentation-marp]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[ai-git-commit]]"
  - "[[marp-advanced]]"
depends_on: []
---

## Overview

Marp (Markdown Presentation Ecosystem) is an open-source toolchain that converts Markdown files into presentation slides (HTML, PDF, PPTX) using a simple `---` separator syntax. It consists of three main components: **Marp Core** (the rendering engine), **Marp CLI** (command-line converter), and **Marp for VS Code** (live-preview extension). The ecosystem is built on the **Marpit** framework, which provides a pluggable, CSS-driven theming system. Marp is MIT-licensed, requires only Node.js (or npx), and works on Windows, macOS, and Linux without configuration.

---

## Core Components

| Component | Package / ID | Role |
|-----------|-------------|------|
| **Marpit** | `@marp-team/marpit` | Skinny base framework — slide parsing, SVG layout, CSS theme engine |
| **Marp Core** | `@marp-team/marp-core` | Extends Marpit — built-in themes, math (MathJax/KaTeX), emoji (Twemoji), GFM tables, auto-scaling |
| **Marp CLI** | `@marp-team/marp-cli` | CLI converter → HTML / PDF / PPTX / PNG; watch mode, server mode |
| **Marp for VS Code** | `marp-team.marp-vscode` | Live preview, IntelliSense for directives, one-click export from VS Code |

---

## Installation (Windows)

### Option 1 — npx (zero install, always latest)

```powershell
# Requires Node.js >= 18
npx @marp-team/marp-cli@latest presentation.md
```

### Option 2 — Global npm install

```powershell
npm install -g @marp-team/marp-cli
marp --version
```

### Option 3 — Scoop (Windows package manager)

```powershell
scoop install marp
marp --version
```

### Option 4 — Standalone binary

Download the `.exe` from the [releases page](https://github.com/marp-team/marp-cli/releases) — no Node.js required.

### VS Code Extension

```
Ext ID: marp-team.marp-vscode
Install: Ctrl+P → ext install marp-team.marp-vscode
```

> **Note:** PDF/PPTX/image export requires a browser (Chrome, Edge, or Firefox) to be installed. Marp detects them automatically.

---

## Slide Syntax

### Basic structure

```markdown
---
marp: true
theme: default
paginate: true
---

# Slide 1 Title

Content of the first slide.

---

## Slide 2

- Bullet point A
- Bullet point B

---

## Slide 3

Regular **Markdown** with `code`, tables, images.
```

### Key rules

- `---` on its own line = new slide (horizontal rule as page separator)
- `marp: true` in front-matter activates the engine (required for VS Code extension)
- First front-matter block (`---…---`) is NOT a slide separator — it's YAML metadata
- All standard CommonMark + GFM syntax works inside slides

### Presenter notes

HTML comments that are NOT directives become presenter notes:

```markdown
# My Slide

Content here.

<!-- Speaker note: Mention the Q3 numbers here. -->
```

### Fitting header

```markdown
# <!-- fit --> This heading stretches to full slide width
```

---

## Directives

Directives configure theme, layout, and per-slide options. They go in front-matter or HTML comments.

### Global directives (apply to whole deck)

```yaml
---
marp: true
theme: gaia          # default | gaia | uncover
size: 16:9           # 16:9 (default) | 4:3
math: mathjax        # mathjax | katex
paginate: true
header: "Q3 Report"
footer: "Confidential — the owner's Team"
style: |
  section {
    font-size: 28px;
  }
---
```

### Local directives (per-slide; apply to current + following slides)

```markdown
<!-- backgroundColor: #1e1e2e -->
<!-- color: white -->
<!-- class: lead -->
```

### Spot directives (underscore prefix = current slide only)

```markdown
<!-- _backgroundColor: #fafafa -->
<!-- _class: lead -->
<!-- _paginate: skip -->
```

### Common local directives reference

| Directive | Description | Example |
|-----------|-------------|---------|
| `paginate` | Show page numbers | `true` / `false` / `skip` / `hold` |
| `header` | Slide header text | `"Project Alpha"` |
| `footer` | Slide footer text | `"© 2026 the owner"` |
| `class` | CSS class on `<section>` | `lead`, `invert` |
| `backgroundColor` | Background color | `#2d2d2d` |
| `backgroundImage` | Background image URL | `url(./bg.jpg)` |
| `backgroundSize` | CSS background-size | `cover`, `contain` |
| `color` | Text color | `white` |

---

## Themes

### Built-in themes (Marp Core)

| Theme | Directive | Character |
|-------|-----------|-----------|
| **default** | `theme: default` | Clean white; body text prominent |
| **gaia** | `theme: gaia` | Colorful header accent, modern |
| **uncover** | `theme: uncover` | Minimal, centered layout |

All built-in themes support `size: 16:9` (1280×720 px) and `size: 4:3` (960×720 px).

### Special CSS classes (built-in themes)

```markdown
<!-- _class: lead -->      # Centered title layout
<!-- _class: invert -->    # Dark/inverted color scheme
<!-- _class: gaia -->      # Gaia-style on non-gaia themes
```

### Custom CSS theme

Create a `.css` file with theme metadata:

```css
/* @theme my-corp-theme */

section {
  background-color: #ffffff;
  color: #333333;
  font-family: "Calibri", sans-serif;
  font-size: 28px;
}

section.lead {
  text-align: center;
  background-color: #003366;
  color: white;
}

h1, h2 {
  color: #003366;
}

footer {
  font-size: 14px;
  color: #999;
}
```

Use it via CLI:

```powershell
marp --theme ./my-corp-theme.css --pdf presentation.md
```

Or in front-matter (after registering in VS Code settings):

```yaml
---
theme: my-corp-theme
---
```

### Inline style overrides (no custom theme file needed)

```yaml
---
marp: true
style: |
  section {
    background: linear-gradient(135deg, #003366, #0066cc);
    color: white;
  }
  h1 { border-bottom: 3px solid #ffcc00; }
---
```

---

## Background Images

```markdown
<!-- Fullscreen background -->
![bg](./background.jpg)

<!-- Background with size -->
![bg cover](./background.jpg)
![bg contain](./background.jpg)
![bg 70%](./background.jpg)

<!-- Background + text side-by-side (split layout) -->
![bg left](./image.jpg)

## Slide with image on the left

Text content appears on the right automatically.

---

<!-- Multiple backgrounds (tiled) -->
![bg](./img1.jpg)
![bg](./img2.jpg)
```

---

## Two-Column Layout

Marp does not have a native column directive, but CSS Grid achieves it:

```markdown
---
marp: true
style: |
  .columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 2rem;
  }
---

<div class="columns">
<div>

## Left Column

- Point A
- Point B
- Point C

</div>
<div>

## Right Column

| KPI | Value |
|-----|-------|
| Revenue | €1.2M |
| Growth | +18% |

</div>
</div>
```

---

## Math Typesetting

```markdown
---
math: mathjax
---

Inline math: $E = mc^2$

Block math:

$$
\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i
$$
```

---

## CLI Reference

### Core conversion commands

```powershell
# HTML (default)
marp presentation.md
marp presentation.md -o output.html

# PDF (requires browser)
marp --pdf presentation.md
marp presentation.md -o report.pdf

# PowerPoint
marp --pptx presentation.md
marp presentation.md -o slides.pptx

# PNG images (one per slide)
marp --images png presentation.md

# First slide only as PNG (for thumbnails/OG images)
marp --image png presentation.md -o cover.png
```

### Development workflow

```powershell
# Watch mode — auto-rebuild on save
marp -w presentation.md

# Server mode — browse slides at localhost:8080
marp -s ./slides/

# Preview window (opens native window)
marp -p presentation.md
```

### Theme and styling

```powershell
# Apply custom CSS theme
marp --theme ./corp-theme.css --pdf presentation.md

# Multiple custom themes in a directory
marp --theme-set ./themes/ --pdf presentation.md
```

### PDF options

```powershell
# Include presenter notes in PDF
marp --pdf --pdf-notes presentation.md

# Add PDF bookmarks/outlines
marp --pdf --pdf-outlines presentation.md

# Allow local file references (images, fonts)
marp --pdf --allow-local-files presentation.md
```

### Export notes as text

```powershell
marp --notes presentation.md -o notes.txt
```

### Configuration file

Save `.marprc.yml` or `marp.config.js` in project root to avoid repeating flags:

```yaml
# .marprc.yml
theme: ./themes/corp.css
pdf: true
allow-local-files: true
```

---

## VS Code Workflow

### Setup

1. Install extension: `marp-team.marp-vscode`
2. Add `marp: true` to front-matter
3. Open preview: `Ctrl+K V` or click the preview icon

### Key features

| Feature | Description |
|---------|-------------|
| **Live preview** | Side-by-side slide preview, updates on save |
| **IntelliSense** | Auto-completion for directives (Ctrl+Space in front-matter) |
| **Hover help** | Hover over any directive for documentation |
| **Diagnostics** | Red underline for unknown themes, deprecated syntax |
| **Export** | Right-click → "Export slide deck" (HTML/PDF/PPTX/PNG) |
| **Custom themes** | Register in `settings.json` → use in front-matter |

### Register custom theme in VS Code

```json
// .vscode/settings.json
{
  "markdown.marp.themes": [
    "./themes/corp-theme.css"
  ]
}
```

### VS Code keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| Open preview | `Ctrl+K V` |
| Toggle Marp feature | Toolbar icon → "Toggle Marp feature" |
| Export (command palette) | `Ctrl+Shift+P` → "Marp: Export slide deck" |

---

## Advanced Features

### Slide transitions (bespoke HTML template)

```markdown
---
marp: true
---

<!-- transition: fade -->

# Slide 1

---

<!-- _transition: slide -->

# Slide 2 — custom transition for this slide only
```

Available transitions: `fade`, `slide`, `cover`, `reveal`, `drop`, `explode`, `flip`, `iris-in`, `iris-out`, `melt`, `overlap`, `pull`, `push`, `rotate`, `swap`, `swoosh`, `wipe`, `zoom` (and more).

### Code block syntax highlighting

````markdown
```python
import pandas as pd
df = pd.read_csv("data.csv")
print(df.describe())
```

```sql
SELECT category, SUM(revenue)
FROM sales
GROUP BY category
ORDER BY 2 DESC;
```
````

### Emoji support

```markdown
Marp renders :rocket: as a Twemoji SVG: 🚀
All Unicode emoji work natively.
```

### headingDivider (auto-split on headings)

```yaml
---
headingDivider: 2
---

# Title Slide

## Section 1

Content...

## Section 2

Content...
```

---

## Use Cases for the owner's Team

| Use Case | Format | Notes |
|----------|--------|-------|
| **Project status reports** | PDF / PPTX | paginate + header/footer with date and project name |
| **Analysis summaries** | HTML | Interactive bespoke template with keyboard nav |
| **Client presentations** | PPTX | corp theme, editable in PowerPoint |
| **Internal sprint reviews** | HTML | Quick: `marp -s ./deck/` served locally |
| **Architecture decision summaries** | PDF | Linked from wiki ADR pages |
| **Technical documentation** | HTML | Deploy as static site |
| **Data reports with tables** | PPTX | Two-column grid layout with data tables |

**Workflow recommendation:**

```
Write .md in VS Code → live preview via extension
→ commit Markdown to Git (version controlled)
→ Export: npx marp --pdf --allow-local-files report.md
→ Share PDF or serve HTML
```

---

## Limitations

| Limitation | Detail |
|------------|--------|
| **PDF/PPTX requires browser** | Chrome, Edge, or Firefox must be installed |
| **No native columns** | Must use CSS Grid via inline `<style>` or custom theme |
| **PPTX content not editable** | Exported as rasterized images; `--pptx-editable` is experimental and needs LibreOffice |
| **No live multi-user collaboration** | Markdown is a file — no real-time co-authoring |
| **Slide transitions browser-only** | Transitions (bespoke template) work in HTML; PDF/PPTX get no transitions |
| **No built-in charting** | Charts must be pre-rendered images or Mermaid (via plugin) |
| **Local file security** | PDF/PPTX conversions block local files by default — need `--allow-local-files` |
| **PPTX fidelity** | Complex CSS (gaia theme gradients) can render poorly in editable PPTX mode |
