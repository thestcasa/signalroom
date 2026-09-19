# SignalRoom adversarial audit

Audit date: 19 September 2026

## Verdict

SignalRoom is a credible, stakeholder-ready portfolio prototype after the repairs in this audit. Its strongest property is not the volume of tactical output, but the traceable and conservative path from pinned source events to suppressed or published evidence. It is not a production club platform: it has one provider adapter, no authentication or operational data store, no adjustment for opponent strength or match state, and no evidence of analyst adoption or sporting impact.

The audit verified 22 Brighton matches, 81,809 events, and 92 attacking corners, plus 34 Leverkusen matches, 137,765 events, and 236 attacking corners. Independent direct-JSON recomputation found zero mismatches across 392 match-metric values. Both cases still publish zero broad tactical-change findings. After correcting SetPieceLab classification and conversion logic, Brighton has three published routine groups and Leverkusen has eight.

## Scope and method

- Inspected every tracked source, configuration, test, generated case artifact, document, outreach asset, and deployment file.
- Compared the local checkout, GitHub `main`, and the Render deployment revision.
- Installed from `uv.lock`, ran lint, tests, coverage, both real-data builds, PDF generation, and Streamlit application tests.
- Recomputed all seven match metrics directly from the pinned raw StatsBomb JSON for all 56 matches without calling SignalRoom metric functions.
- Recounted matches, events, event IDs, attacking corners, shot-producing sequences, and rebound shots from source records.
- Rebuilt all 16 case artifacts twice and compared SHA-256 hashes.
- Exercised both live cases and all five application tabs, inspected browser semantics and console output, and reviewed the Render deploy, logs, configuration, and metrics.
- Audited the resolved development environment with `pip-audit`.
- Rendered and visually inspected the revised one-page stakeholder PDF.

## Verified results

| Check | Result |
| --- | --- |
| Lint | Pass |
| Tests | 29 passed |
| Coverage | 90% total |
| Real-data case builds | Pass for Brighton and Leverkusen |
| Repeated artifact build | Byte-identical across 16 files |
| Independent metric recomputation | 0 mismatches across 392 values |
| Strict JSON parsing | Pass, no `NaN` or `Infinity` |
| Evidence and narrative grounding | Pass for both bundles |
| Optional dependency audit | No known vulnerabilities after upgrades |
| PDF | One A4 page, visually verified, text extraction verified |
| Final live deployment | Commit `7a3721fa`, deploy `dep-damt2f97lnhs73dmfh40`, live and browser-verified |
| LLM-free operation | Verified, no key or external model dependency exists |

## Most important findings and repairs

1. `shot_rate` counted total shots rather than shot-producing corner sequences. Two Brighton rebound shots and five Leverkusen rebound shots inflated the claimed conversion measure. The pipeline now reports `corners_with_shot`, sequence conversion, total shots, and xG separately.
2. Long deliveries ending before x=108 were silently labeled short, including deliveries close to 40 pitch units. Short corners are now defined only by first-delivery length at or below 15 units; missing length becomes `unknown`.
3. A constant baseline and a different constant recent window produced infinite Hedges g, which could both overstate evidence and create non-standard JSON. Undefined effects now serialize as `null` and are suppressed explicitly.
4. The committed generated timestamp made identical analytical builds differ. Runtime timestamps were removed from analytical bundles and reports; the pinned source revision is shown instead.
5. The original 15-test suite left ingestion, the complete pipeline, charts, CLI, and cache failure modes effectively untested. The repaired suite has 29 tests, 90% coverage, a deterministic end-to-end pipeline fixture, cache recovery coverage, and CI.
6. Small coral and teal text failed WCAG AA contrast against the paper background, chart images had meaningless `alt="0"`, and the visual hero was not an `h1`. Colors, image rendering, alternative text, and heading semantics were repaired.
7. The window-comparison chart placed xG and count metrics on a shared raw scale. It now uses comparable Hedges g values and annotates each row with the original baseline and recent values.
8. Corrupt cached JSON failed immediately. Cache entries are now reacquired and written atomically.
9. Configuration slugs could escape the output directory. Configuration validation now restricts slugs and enforces declared sample minima.
10. The live Render service was created outside the Blueprint. Its recorded build command and empty health-check path differ from `render.yaml`. The canonical Blueprint is repaired and lock-based, but the existing service settings require reconciliation in Render.

The machine-readable register in `audit/findings.json` contains reproduction and verification detail for every finding.

Browser evidence is retained in `audit/screenshots/live-before.jpg` and `audit/screenshots/live-after.jpg`. The final deployment was exercised across both historical cases and all five application tabs. The final release also corrected an artifact publication-path defect that had caused a UTF-8 decode error in the first deployed extension revision.

## Analytical validity

The seven metric formulas reproduce exactly from source data for both cases. Baseline and recent windows are chronological and non-overlapping. Bootstrap and permutation randomness is seeded. Evidence IDs resolve to ingested event IDs, and the deterministic narratives match their structured values.

The zero-finding result is genuine, not a broken pipeline. Brighton effects remain approximately -0.35 to 0.42 and fail magnitude, stability, sensitivity, or multiple-comparison gates. Leverkusen has several moderate descriptive effects, but none pass the configured multiple-comparison rule. The system correctly abstains.

Important limits remain. Results are schedule-conditional and do not control for opponent quality, score state, venue, personnel, or coaching context. Set-piece groups are deterministic descriptive buckets, not learned tactical archetypes. Confidence intervals describe routine share uncertainty, not effectiveness or causality. These limits are now kept explicit.

## Engineering and operational assessment

The architecture is proportionate for a portfolio MVP: provider parsing stops in the adapter, internal models feed metrics and SetPieceLab, and validated bundles feed both the app and static reports. Raw data is excluded from git, the source revision is pinned, and no secrets were found.

The runtime remains intentionally simple and stateless. This is appropriate for two historical cases, but it also means there is no authentication, persistence, job execution, observability layer, or controlled ingestion workflow. Those would be unnecessary until a real analyst workflow demands them.

The free Render service cold-started in roughly 30 seconds during browser testing. That is acceptable for a public demo with a warning, but it weakens a time-sensitive stakeholder walkthrough. The first live deployment had no error logs and used about 100 to 240 MB of memory during observed periods.

## Residual risks

- The existing Render service has configuration drift from the repository Blueprint, specifically its build command and missing health-check path.
- Missing movement endpoints or shot xG are now visible in validation, but broad metric publication is not yet automatically disabled per affected metric.
- Provider neutrality is an architectural boundary, not demonstrated interoperability. Only StatsBomb is implemented.
- The app does not offer a first-class briefing download; CSV downloads are Streamlit table controls rather than a deliberate stakeholder export workflow.
- Mobile behavior is supported by CSS and Streamlit layout, but the cloud browser did not expose a mobile viewport control for a complete device matrix.
- The free hosting cold start remains a stakeholder-experience risk.
- No external football analyst has evaluated whether the routine definitions or evidence presentation improve a real preparation task.

## Final assessment

SignalRoom should be presented as an audited historical analysis prototype and evidence-browser, not as AI that discovers tactics or a production-ready club platform. The corrected project demonstrates sound data acquisition, analytical restraint, source traceability, reproducible reporting, testing, and stakeholder communication. That is a strong portfolio signal for applied analytics and data engineering.

The recommended next milestone is a narrow opponent-preparation comparison inside SetPieceLab: compare one selected team’s routine distribution and shot-producing sequences against a competition baseline, expose the underlying sequences, and validate the briefing with two or three football analysts. Do not add an LLM or several broad tactical modules before that workflow proves useful.

See `audit/ROADMAP.md`, `audit/STAKEHOLDER_ASSESSMENT.md`, and `audit/CHANGELOG.md` for concise follow-on material.

## Dead-ball intelligence extension audit

The product extension was rebuilt from the pinned StatsBomb Open Data cache on 18 September 2026. It now writes schema `1.2.0` bundles with 126 Brighton and 310 Leverkusen attacking final-third dead-ball sequences across four event-defined categories: corners, wide free kicks, indirect near-box free kicks, and direct free-kick shots. Independent raw-event recounts matched every category count: Brighton 92 / 19 / 11 / 4 and Leverkusen 236 / 40 / 13 / 21.

The audit specifically falsified restart classification, sequence linkage, first-contact and second-phase extraction, strict JSON, evidence references, repeat-build hashes, app rendering, and ML publication. Both cases produced finite strict JSON, all evidence IDs resolved to source event IDs, and two consecutive real-data builds were byte-identical. The exploratory profile is suppressed because no complete peer feature matrix is loaded. This is the correct product state, not a missing chart.

Residual risks are deliberate and documented: free-kick labels are location buckets rather than referee-certified direct/indirect labels; first contact is the first recorded contact-like event rather than a verified aerial touch; event data cannot verify off-ball movement, screens, marking, or intent; and no competition prevalence, tracking, video, or external analyst validation is claimed. The current Render configuration drift and free-plan cold start remain operational risks from the prior audit.
