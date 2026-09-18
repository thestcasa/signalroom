# Evaluation plan

## Automated checks

- Source schema and unique event IDs
- Monotonic event ordering
- Metric boundaries and pass-completion rules
- Corner sequence termination
- Non-overlapping temporal windows
- Bootstrap and false-discovery calculations
- Sensitivity-window consistency
- Minimum-sample suppression
- Evidence IDs resolve to ingested source events
- Generated narratives exactly match structured values
- Configuration portability across two competitions

## Real-data acceptance

Both checked-in configurations must build from an empty cache. The interactive interface must load both derived bundles. The static report and screenshots must display the same values as `bundle.json`.

## Statistical interpretation

Intervals quantify match-to-match sampling variability within the selected historical schedule. They do not account for every confounder, including opponent strength, score state, injuries, coaching changes, or selection. The system identifies analyst review candidates, not causal tactical effects or predictive sporting value.

References: Benjamini and Hochberg (1995), DOI `10.1111/j.2517-6161.1995.tb02031.x`; Wilson (1927), DOI `10.1080/01621459.1927.10502953`; Hedges (1981), DOI `10.3102/10769986006002107`.

