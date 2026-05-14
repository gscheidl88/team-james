---
name: writing-clearly-and-concisely
description: "Apply Strunk's Elements of Style rules + AI-writing anti-patterns when writing any prose for humans: documentation, wiki pages, reports, commit messages, error messages, UI text. Use when writing sentences a human will read."
agent: all
tools_required: []
wiki_ref: "[[writing-style]]"
version: "1.0"
source: "https://github.com/softaworks/agent-toolkit/tree/main/skills/writing-clearly-and-concisely"
---

# Skill: Writing Clearly and Concisely

**Category:** Communication  
**Trigger:** ANY task producing prose for humans — documentation, wiki, reports, plans, commit messages, error messages  
**Owner:** All agents (James, Analyst, Developer, Researcher)

---

## Core Principle

**Write with clarity and force. Omit needless words.**

Every word must earn its place. If a sentence says the same thing with five words as with ten, use five.

---

## When to Use This Skill

Use it when writing:
- Wiki pages (`wiki/*.md`)
- Plans (`plans/*.md`)
- `MEMORY.md` and `USER.md` entries
- Commit messages
- Code comments (the few that are needed)
- Any report, summary, or explanation
- Responses where the owner will copy/paste text externally

**If you're writing sentences a human will read → activate this skill.**

---

## The 8 Rules That Matter Most (Strunk)

Derived from *The Elements of Style* — the timeless source.

| # | Rule | Example |
|---|------|---------|
| 1 | **Use active voice** | ❌ "The report was written by the agent." → ✅ "The agent wrote the report." |
| 2 | **Put statements in positive form** | ❌ "He was not very often on time." → ✅ "He usually came late." |
| 3 | **Use definite, specific, concrete language** | ❌ "A period of unfavorable weather set in." → ✅ "It rained every day for a week." |
| 4 | **Omit needless words** | ❌ "the fact that" → ✅ delete it |
| 5 | **Keep related words together** | Subject and verb should not be separated by many words |
| 6 | **Place emphatic words at end of sentence** | The end carries weight. Start with context, end with the point. |
| 7 | **One paragraph per topic** | Don't mix ideas. If you switch topics, start a new paragraph. |
| 8 | **Begin paragraph with topic sentence** | State the main point first, then support it. |

---

## AI Writing Patterns — Never Use These

These are statistical averages. Using them makes writing sound generated, not thought.

### Banned Words/Phrases
```
pivotal, crucial, vital, testament to, enduring legacy
ensure reliability, showcase features, highlight capabilities  
groundbreaking, seamless, robust, cutting-edge, state-of-the-art
delve, leverage, multifaceted, foster, realm, tapestry, nuanced
it is important to note, it is worth mentioning, needless to say
```

### Banned Patterns
- **Empty -ing openers:** "Ensuring reliability, the system..." → just say what it does
- **Promotional adjectives:** "This powerful solution..." → say what it actually does
- **Passive hedging:** "It could be argued that..." → argue it, or don't
- **Excessive bullets:** not everything is a list; prose often communicates better
- **Bold overuse:** bolding every other phrase defeats the purpose; bold only the truly critical

### The Substitution Test
Before using any of the banned words, ask: *what does this actually mean?*  
If you can replace it with a specific, concrete phrase — do it.

```
❌ "This leverages a robust pipeline to ensure seamless data flow."
✅ "The pipeline reads from Kafka, transforms in DuckDB, and writes to S3 within 2 seconds."
```

---

## Quick Reference: Common Corrections

| Don't write | Write instead |
|------------|--------------|
| "the fact that" | delete it |
| "in order to" | "to" |
| "due to the fact that" | "because" |
| "at this point in time" | "now" |
| "in the event that" | "if" |
| "It is important to note that" | delete + just say it |
| "make an attempt" | "try" |
| "prior to" | "before" |
| "subsequent to" | "after" |
| "utilize" | "use" |
| "the majority of" | "most" |

---

## For Wiki Pages (owner Team Standard)

Apply these rules in addition to Strunk:

1. **L0 (description field):** One sentence. Active verb. No "This page covers..."  
   ❌ "This page covers the topic of embedded databases."  
   ✅ "Compares embedded databases for local analytics: DuckDB, SQLite, LanceDB, Kuzu."

2. **L1 (Overview section):** 2–5 sentences. State the key insight immediately.  
   Start with what it IS, not how you found it.

3. **Headers:** Use sentence case, not Title Case.  
   ❌ "Key Benefits and Limitations"  
   ✅ "Key benefits and limitations"

4. **Avoid hedging in facts:**  
   ❌ "It seems that DuckDB might be faster in some cases."  
   ✅ "DuckDB outperforms SQLite on analytical queries over 100k rows (TPC-H benchmark)."

---

## Checklist

- [ ] Every sentence uses active voice (or has a reason not to)
- [ ] No banned AI words present
- [ ] No "in order to", "due to the fact that", "utilize"
- [ ] First sentence of each paragraph states the main point
- [ ] Numbers and specifics replace vague qualifiers
- [ ] Text length is the minimum needed — nothing more
- [ ] If it's a wiki page: `## Overview` is 2–5 sentences, concrete

---

## Further Reading

Source material from softaworks/agent-toolkit:
- `signs-of-ai-writing.md` — Comprehensive Wikipedia editor guide to AI-generated text patterns
- `elements-of-style/` — Full Strunk text by chapter

## Anti-patterns

- Do not activate this skill when a simpler direct answer or a different specialist skill is a better fit.
- Do not hide assumptions, uncertainty, or missing inputs behind confident-sounding prose.
- Do not skip the required validation, evidence, or operator handoff that makes the output usable.
- Do not turn examples into universal rules without checking whether the current task actually matches them.