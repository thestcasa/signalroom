# Prioritized roadmap (superseded)

Current implementation status is in `../docs/IMPLEMENTATION_PLAN.md`. This file describes the earlier roadmap.

## 1. Opponent-preparation comparison, delivered

- User problem: analysts need to know which set-piece behaviors are unusually frequent or recently changing, with video/event evidence they can inspect.
- Target user: first-team or academy opposition analyst.
- Expected value: turns the existing descriptive inventory into a concrete preparation workflow without expanding beyond the strongest module.
- Evidence: SetPieceLab already produces stable, traceable groups; the current app lacks a comparison context.
- Implementation: configurable team and window, competition or opponent baseline, share differences with uncertainty, stability checks, and direct sequence review/export.
- Data: existing event feed for an initial historical validation; richer provider access later.
- Risks: schedule effects, small samples, routine taxonomy sensitivity, and false causal interpretation.
- Effort: medium, approximately one focused iteration after metric design review.
- Validation: task-based review with two or three analysts, blinded correctness checks, and known-fixture regression tests.
- Priority: P0. Delivered in the current extension with a within-team baseline, evidence filters, stability checks, and briefing export.

## 2. Metric-level data-quality gates, partially delivered

- Problem: missing endpoints or xG can silently lower derived metrics even when dataset validation reports them.
- Value: prevents incomplete provider records from becoming publishable comparisons.
- Implementation: completeness counters per metric and match, configurable tolerance, explicit suppression reasons, and UI diagnostics.
- Effort: small to medium.
- Priority: P0 correctness work. Set-piece routine-share and shot-xG gates are delivered; the broader seven-metric publication contract still needs metric-specific source completeness fields.

## 3. Shareable briefing export, delivered

- Problem: stakeholders cannot download the selected interactive state as a concise evidence-linked briefing.
- Implementation: deterministic HTML/PDF export with selected case, definitions, evidence references, and limitations.
- Effort: medium.
- Priority: P1. Delivered as deterministic self-contained HTML; reliable PDF remains optional follow-up work.

## 4. Second provider adapter, build only with a licensed sample

- Problem: provider neutrality is currently structural rather than demonstrated.
- Implementation: map a second provider into the internal contract and run the same known-fixture suite.
- Risk: semantic differences can invalidate apparently equivalent metrics.
- Priority: P1 when legitimate data access exists.

## 5. Analyst annotations, defer

Useful only after repeated use demonstrates a need to save, reject, or discuss sequences. A database and identity layer would then be justified.

## Do not build now

- Ungrounded LLM tactical narratives
- Several new tactical modules
- Outcome prediction or causal effectiveness claims
- A multi-tenant production platform

These would add surface area before SignalRoom has validated one recurring analyst decision.

## Dead-ball platform follow-on

- Add complete peer/competition loading only after coverage completeness and denominator rules are verified.
- Add a second licensed provider adapter or a public tracking adapter, with semantic known-fixture tests.
- Add 360/tracking capability only where the source package actually contains those positions.
- Add video references only after legitimate synchronized video access exists.
- Extend the same contract to attacking throw-ins, goal kicks, kick-offs, penalties, defensive restarts, and defensive profile review.
