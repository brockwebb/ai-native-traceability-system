# Design Decision: AI-First Capture

**Date:** 2025-02-02
**Status:** Approved
**Scope:** System-wide design principle

## Decision

The trace system SHALL be designed for AI-first capture with minimal human involvement.

## Principle

> Default behavior requires zero human discipline. AI infers, proposes, and captures during normal work. Value is delivered before the human does anything extra.

## Implications

### 1. Defaults Over Configuration
- `trace init` auto-detects project type and selects appropriate template
- Bootstrap scan runs automatically
- Sensible tags inferred from file location and content

### 2. Capture During Work, Not After
- CC skill auto-registers files on create/modify
- Relationships inferred from imports, references, mentions
- No separate "documentation phase"

### 3. Propose Freely, Approve Lazily
- AI proposes links with low friction (confidence threshold, not certainty)
- Proposals accumulate without blocking work
- Human batch-approves at natural breakpoints (or auto-approve by policy)

### 4. Proactive, Not Reactive
- Impact warnings surface before risky changes
- Health issues surfaced without being asked
- Orphans and gaps highlighted automatically

### 5. Templates Are "Good Enough"
- Out-of-box templates work for most projects
- Tailoring is advanced/optional, not required
- IEEE-style tailoring available but not default path

## Constraints on Future Features

All features MUST:
- Work without human remembering to invoke them
- Provide value with zero configuration beyond init
- Default to AI-inferred behavior
- Make human intervention optional, not required

Features SHOULD:
- Surface insights proactively
- Batch operations to reduce approval fatigue
- Learn from project patterns over time (future)

## Rationale

Adoption fails when tools require discipline. Git succeeded because you can't collaborate without it — it's mandatory friction. Trace must succeed by being invisible friction — value appears without effort.

Human discipline doesn't scale. AI attention does.

## References

- Roadmap: v0.2+ features
- Methodology templates design decision
- MCP parity principle (task 006)
