# Historical case study

## Question

Can public event data produce a concise, auditable briefing without turning ordinary variation into a tactical claim?

## Cases

- Brighton & Hove Albion Women, FA WSL 2023/24: primary historical example.
- Bayer Leverkusen, Bundesliga 2023/24: portability check.

## Method

SignalRoom compares a recent match window with the immediately preceding, non-overlapping baseline. Seven metrics pass through effect-size, bootstrap direction, sensitivity, multiple-comparison, and evidence gates. SetPieceLab groups attacking corners by delivery side, short/direct choice, and target zone, requiring at least four examples per published routine.

## Result

Brighton: all seven broad changes were suppressed. Their standardized effects ranged from -0.35 to 0.42, and none cleared the combined magnitude, stability, sensitivity, and multiple-comparison gate. This is not evidence that tactics did not change. It means this design should not promote a broad change from the available sample.

SetPieceLab processed 92 Brighton attacking corners. Four groups met the minimum cluster size: right/direct/central (45, 17 shots, 1.91 xG), left/direct/central (34, 10 shots, 1.54 xG), right/direct/near-side (4, 2 shots, 0.22 xG), and left/short/short-option (4, 1 shot, 0.15 xG). Each output has concrete source sequences.

The same pipeline processed Bayer Leverkusen through configuration only: 34 matches, 236 attacking corners, and seven published routine groups. Its broad comparisons were also suppressed after false-discovery control.

## Interpretation

The output is a triage layer for analyst review. It is not a causal explanation, a prediction of match outcomes, or current tactical advice.

## Deliverables

- Interactive Streamlit application: run `make demo`
- Static case reports: `artifacts/cases/*/report.html`
- Shareable one-page PDF: `outreach/SignalRoom_Case_Study.pdf`
- Machine-auditable bundles: `artifacts/cases/*/bundle.json`
