# Claims ledger

This ledger reflects the generated bundles dated 18 September 2026.

| Claim | Status | Evidence | Allowed wording |
| --- | --- | --- | --- |
| WSL 2023/24 includes 22 Brighton matches | Verified | Official match records, competition 37 / season 281 | State directly |
| Brighton case contains 92 attacking corners | Verified | `brighton-wsl-2023-24/bundle.json` and 92 source corner-pass events | State as historical sample count |
| Three Brighton corner routine groups pass n >= 4 | Verified | 45, 35, and 6 examples; 6 corners remain in suppressed groups | State with descriptive qualification |
| No Brighton broad change passes the publication gate | Verified | All seven comparisons have absolute standardized effect < 0.5 and/or fail stability/FDR gates | State as abstention, not evidence of no tactical change |
| Leverkusen validates configuration portability | Verified | 34 matches, 236 corners, eight published routine groups through the same pipeline | State directly |
| SetPieceLab conversion is not inflated by rebounds | Verified | Conversion counts shot-producing corner sequences; total shots are reported separately | State with the sequence-window definition |
| SignalRoom is club-independent | Verified in code | Team and IDs occur in TOML and derived bundles, not metric logic | State directly |
| Published routine outputs are evidence-linked | Verified | Grounding validator passes and every routine reference resolves to source event IDs | State directly |
| Product improves match preparation | Hypothesis | Not measured | Do not claim as verified |
| Product predicts sporting outcomes | Not measured | None | Do not claim |
| Tactical changes are causal | Not measured | None | Do not claim |
| Historical cases reflect current tactics | False | Historical seasons only | Explicitly disclaim |
