# SignalRoom

SignalRoom converts football event data into short, evidence-linked historical briefings. It is a club-independent applied analytics case study by Alessandro Casadei.

**Live demo:** https://signalroom-tka1.onrender.com

The product follows a focused opponent-preparation workflow: choose a historical opponent case, compare the latest team window with the previous team window, and open the event sequences behind any routine difference. It suppresses weak findings instead of filling a report.

## What works

- Cache-first StatsBomb Open Data ingestion
- Provider-neutral match and event models
- Seven versioned team metrics
- Non-overlapping baseline and recent windows
- Match-level bootstrap intervals, permutation tests, effect sizes, sensitivity checks, and false-discovery control
- Deterministic attacking-corner routine groups
- Event-level evidence references for every published finding
- Grounded, template-based reports that need no LLM
- Interactive Streamlit analyst interface and static HTML exports
- Configurable routine comparison with bootstrap intervals, sensitivity labels, data-quality gates, and deterministic briefing download
- Two configurations: Brighton Women in the 2023/24 WSL and Bayer Leverkusen in the 2023/24 Bundesliga

## Quick start

```bash
make setup
make test
make build-cases
make demo
```

Open the local URL printed by Streamlit. Raw event files are downloaded from the official source into `data/cache/` and are not committed.

## Deployment

`render.yaml` is the canonical specification for a single free-plan Render web service with no secrets or external infrastructure. It binds Streamlit to Render's `PORT` and uses `/_stcore/health` for health checks. Existing services created outside a Blueprint must be checked separately for configuration drift. Applying the Blueprint requires selecting the intended Render workspace first:

`https://dashboard.render.com/blueprint/new?repo=https://github.com/thestcasa/signalroom`

Free services can spin down after inactivity and cold-start on the next request. The verified local path remains `make demo`.

To analyze another available team, copy a TOML file in `configs/`, change the team, competition, and season identifiers, then run:

```bash
.venv/bin/python -m signalroom.cli build --config configs/your_case.toml
```

## Repository map

- `src/signalroom/adapters/`: source-specific ingestion
- `src/signalroom/models.py`: internal data contract
- `src/signalroom/metrics.py`: metric definitions and calculations
- `src/signalroom/statistics.py`: change detection and suppression
- `src/signalroom/setpieces.py`: corner sequence and routine analysis
- `src/signalroom/opponent.py`: comparison baseline, uncertainty, completeness, and stability logic
- `src/signalroom/evidence.py`: event trace construction
- `src/signalroom/reporting.py`: deterministic narrative and grounding checks
- `app.py`: analyst interface
- `artifacts/cases/`: reproducible derived case outputs, no raw event dataset
- `docs/`: product, data, analytics, evaluation, architecture, and decision records
- `outreach/`: stakeholder-ready material

## Honest positioning

SignalRoom supports teams and competitions available through its implemented event-data adapters. The initial version uses StatsBomb Open Data and is designed so additional providers can be added later.

This repository is not affiliated with or endorsed by Brighton & Hove Albion, Bayer Leverkusen, StatsBomb, Hudl, or any other club or data provider. The case studies are historical and are not current tactical advice.

## Opponent-preparation workflow

The default comparison is the selected team's latest chronological match window against its previous chronological window. This is a valid within-team baseline using the source data already bundled in each case. The current bundles do not include every competition match, so SignalRoom does not fabricate a competition-wide routine baseline. A future source expansion can add that baseline after verifying coverage for all teams and matches.

The interface publishes a routine only when the recent sample, routine-share completeness, and comparison evidence gates pass. Bootstrap intervals show uncertainty around share differences. Nearby-window sensitivity produces stakeholder labels such as `stable`, `directionally consistent`, `sensitive to window selection`, or `sample too small`.

The Evidence room filters by routine, opponent, and shot outcome, shows the ordered event sequence and pitch view, and exports source event identifiers. The briefing download is deterministic HTML, not an automated tactical essay.

## Data terms and attribution

The source data is [StatsBomb Open Data](https://github.com/hudl/open-data). Its README requires StatsBomb attribution and use of its logo when publishing analysis. The data remains subject to the [StatsBomb Public Data User Agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf). SignalRoom does not redistribute the raw dataset.

The repository's MIT license applies to SignalRoom's original source code only. It does not relicense StatsBomb data or branding.
