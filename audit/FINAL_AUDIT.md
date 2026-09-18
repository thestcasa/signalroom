# SignalRoom extension adversarial audit

Audit date: 18 September 2026

## Scope

The extension was audited after implementation against the prior audit, current source, regenerated case bundles, tests, and live application path. The audit attempted to falsify routine denominators, comparison values, suppression decisions, stability labels, evidence references, briefing claims, and frontend rendering.

## Results

| Check | Result |
| --- | --- |
| Ruff lint | Pass |
| Tests | 27 passed |
| Coverage | 89% total, no regression from prior audit |
| Real-data rebuilds | Brighton and Leverkusen pass |
| Strict JSON | Pass, no NaN or Infinity |
| Routine evidence references | Pass, all SP identifiers resolve inside bundles |
| Deterministic briefing export | Pass, identical input state produces identical HTML |
| Existing case artifact reproducibility | Pass after regenerated outputs |
| Frontend AppTest | Pass for both cases |
| Independent routine denominator check | Pass |
| Analyst validation | Not yet performed |

## Falsification attempts

- Recomputed routine shares from stored `SP-` sequences using all corners in each window as denominators. No mismatch found.
- Checked zero-baseline shares. Relative difference is `null`, not infinite.
- Checked below-minimum routine samples. The comparison is suppressed with an explicit reason.
- Checked missing quality metadata. The comparison reports a conservative default and the bundle-level quality display remains visible.
- Checked evidence IDs in comparison rows and exports. IDs resolve to bundle sequences and their source event IDs.
- Checked export values against structured comparison values. The export is generated directly from the same structured rows.
- Checked mobile-facing CSS for overflow-prone hero and split layouts. Responsive rules collapse the major multi-column sections.

## Residual risks

- The comparison baseline is within-team, not competition-wide, because the current source bundles do not contain every competition match. This limitation is visible and documented.
- Set-piece metric gates are implemented, but the broader seven-metric change-comparison layer still needs metric-specific completeness denominators.
- Stability labels are sensitivity indicators, not proof of generalization.
- No video integration, analyst adoption, club use, or sporting impact is claimed.
- Render configuration drift and free-plan cold start remain operational risks from the previous audit and require dashboard verification outside the repository.
