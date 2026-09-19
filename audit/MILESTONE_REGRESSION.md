# Evidence Integrity and WSL Peer Baseline regression report

Audit baseline: commit `6d751282bdebc5e1e272ae1ca7395ff0ab6edb7f`

| ID | Status | Implementation and verification |
| --- | --- | --- |
| F01 | Repaired | Every displayed group and restart reference resolves against the complete derived evidence collection; builds fail on a missing ID. |
| F02 | Repaired | Generic review-question generation was removed. Predicate validation checks every reference. |
| F03 | Repaired | Opponent events rotate into the selected-team-attacks-right frame; tests cover both teams. |
| F04 | Removed | The second-phase field and output were deleted. |
| F05 | Removed | Immediate post-delivery events and shots are represented directly, without phase inference. |
| F06 | Repaired | Player roles are explicit and selected-team scoped. |
| F07 | Repaired | Target lanes use x and y boundaries. |
| F08 | Repaired | Corner target classification includes depth and width and is called a lane. |
| F09 | Repaired | Action-specific outcomes, body part, height, technique, and unavailable states are preserved. |
| F10 | Repaired | Corner group intervals resample complete matches and expose the resampling unit. |
| F11 | Repaired | Review eligibility requires sample, match support, effect, interval, nearby-window direction, evidence, and quality. |
| F12 | Repaired | One analysis context drives shortlist, evidence filtering, notes, and export. |
| F13 | Repaired | Central final-third free-kick pass replaces indirect claims; legal status is unavailable. |
| F14 | Repaired | Direct free-kick shot conversion is null and absent from conversion rankings. |
| F15 | Repaired | Export contains current context and resolvable derived evidence references. |
| F16 | Repaired | Missing quality metadata fails completeness instead of defaulting true. |
| F17 | Repaired | Every sequence has termination and optional censoring reasons. |
| F18 | Repaired | Capability copy distinguishes event data, snapshots, tracking, visibility, and unsupported movement inference. |
| F19 | Repaired | Progressive actions use provider pitch-unit terminology and remain optional context. |
| F20 | Repaired | Broad metric publication requires false-discovery control and an interval excluding zero. |
| F21 | Repaired | Limitations and peer availability derive from the selected case and coverage ledger. |
| F22 | Repaired | Outputs are recorded delivery groups; nearby-window direction replaces stability claims. |
| F23 | Repaired | Explicit null checks preserve zero-valued coordinates. |
| F24 | Repaired conservatively | Public artifacts allow attributed aggregates and derived summaries; raw records, provider event IDs, and exact excerpts are blocked. |

Acceptance criteria 1 to 15 are implemented and automatically checked. Criterion 16 is a claim gate: independent analyst testing has not occurred, so no validation claim is made.

No excluded ML, computer-vision, tracking, live-feed, generalized-ingestion, recommendation, or LLM feature was added.

