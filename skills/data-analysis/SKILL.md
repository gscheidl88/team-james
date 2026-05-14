---
name: data-analysis
description: "SQL patterns, DuckDB analytics, pandas profiling, BI reporting, and exec summary templates for the owner's analyst work"
agent: Analyst
tools_required: [uv, duckdb, python]
wiki_ref: "[[research-synthesis-memory-systems]]"
version: "1.0"
---

# Skill: Data Analysis

**Category:** Data & Analytics  
**Trigger:** Any analysis task involving data exploration, SQL, reporting, or visualization  
**Owner:** Analyst Agent

---

## When to Use This Skill

- the owner provides a dataset (CSV, Excel, database table) and wants insights
- SQL query needed for business reporting
- KPI dashboard design
- Financial or operational analysis
- Data quality investigation

---

## Standard Analysis Workflow

```
1. UNDERSTAND  → What question are we answering?
2. PROFILE     → Shape, types, nulls, distributions
3. CLEAN       → Handle missing, duplicates, outliers
4. ANALYZE     → Aggregate, compare, correlate
5. INTERPRET   → What does it mean for the business?
6. PRESENT     → Table / chart + narrative summary
```

---

## Data Profiling Template (Python/pandas)

```python
import pandas as pd

def profile(df: pd.DataFrame) -> None:
    print(f"Shape: {df.shape}")
    print(f"\nTypes:\n{df.dtypes}")
    print(f"\nNull counts:\n{df.isnull().sum()}")
    print(f"\nDescriptive stats:\n{df.describe()}")
    print(f"\nDuplicates: {df.duplicated().sum()}")
```

---

## SQL Analysis Patterns

### Trend over time
```sql
SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*)                         AS count,
    SUM(amount)                      AS revenue
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 1
ORDER BY 1;
```

### Top-N with share
```sql
WITH totals AS (
    SELECT SUM(revenue) AS total FROM sales
)
SELECT
    category,
    SUM(revenue)                           AS revenue,
    ROUND(SUM(revenue) / totals.total * 100, 1) AS pct_share
FROM sales, totals
GROUP BY category, totals.total
ORDER BY revenue DESC
LIMIT 10;
```

### Cohort / period-over-period
```sql
SELECT
    category,
    SUM(CASE WHEN period = 'current' THEN revenue END)  AS current_rev,
    SUM(CASE WHEN period = 'prior'   THEN revenue END)  AS prior_rev,
    ROUND(
        (SUM(CASE WHEN period = 'current' THEN revenue END) /
         NULLIF(SUM(CASE WHEN period = 'prior' THEN revenue END), 0) - 1) * 100, 1
    ) AS pct_change
FROM sales_periods
GROUP BY category;
```

---

## Report Structure (Exec Summary)

```markdown
## [Report Title]
**Date:** {date} | **Prepared by:** Analyst Agent

### Key Findings
1. {Most important insight — with number}
2. {Second insight}
3. {Third insight}

### Detail
{Tables and charts}

### Recommendation
{Clear action based on findings}
```

---

## Anti-patterns

- **Skipping profiling** — jumping straight to analysis without checking shape, nulls, and types; produces silent garbage results.
- **Presenting numbers without interpretation** — tables and aggregates with no narrative = no value for the owner.
- **Mixing cleaning and analysis steps** — makes results unreproducible; always separate CLEAN from ANALYZE.
- **Ignoring outliers** — not flagging high-variance or extreme values distorts aggregates and misleads conclusions.
- **Using pandas for large files** — anything >500 MB should use DuckDB directly; pandas will OOM or be unacceptably slow.
- **Hardcoding date ranges** — always parameterize time windows; hardcoded dates break on next run.
- **Writing SQL that depends on column order** — always reference columns by name, not position.

---

## Checklist

- [ ] Data shape stated upfront (rows × columns)
- [ ] Null / quality issues flagged before analysis
- [ ] Numbers interpreted (not just listed)
- [ ] Reproducible SQL or Python code included
- [ ] Outliers / anomalies explicitly acknowledged
- [ ] Clear recommendation or next step provided
- [ ] Output readable by the owner without context (self-contained summary)
