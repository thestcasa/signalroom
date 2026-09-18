# Analytics specification

Metric version: `1.0.0`. StatsBomb pitch coordinates are 120 by 80 and oriented in the attacking direction for each team.

| Metric | Exact rule |
| --- | --- |
| Shots | Count team `Shot` events, including penalties |
| Expected goals | Sum `shot.statsbomb_xg` |
| Final-third entries | Completed pass or carry crossing from x < 80 to x >= 80 |
| Box entries | Completed pass or carry entering x >= 102 and 18 <= y <= 62 from outside |
| Progressive actions | Completed pass or carry gaining at least 15 x units |
| Build-up exits | Completed pass or carry starting at x <= 40 and ending at x >= 60 |
| High regains | `Ball Recovery` or `Interception` recorded at x >= 80 |

An absent pass outcome means complete, consistent with the source schema. Carries are treated as complete recorded actions.

## Change gate

- Baseline and recent windows are chronological and non-overlapping.
- Resampling unit: match.
- Publish when absolute bias-corrected standardized effect is at least 0.5, bootstrap direction probability is at least 0.80, and at least two of three recent-window sensitivity checks agree.
- In addition, require Benjamini-Hochberg q <= 0.20, or a standardized effect of at least 0.8 with direction probability at least 0.90.
- Require at least three retrievable recent evidence sequences.

## SetPieceLab v1

An attacking corner begins with a team pass whose subtype is `Corner`. The sequence continues within the same period and possession for at most 20 seconds and 17 subsequent events. Routines are grouped by delivery side, short/direct choice, and target zone. A cluster needs at least four corners. Shares receive 95% Wilson intervals. Output is descriptive, not causal.

