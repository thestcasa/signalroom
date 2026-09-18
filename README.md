# SignalRoom

SignalRoom converts football event data into short, evidence-linked historical briefings. It is a club-independent applied analytics case study by Alessandro Casadei.

The MVP deliberately takes a narrow path: cautious match-window change detection plus a deeper `SetPieceLab` module for attacking corners. It suppresses weak findings instead of filling a report.

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
- Two configurations: Brighton Women in the 2023/24 WSL and Bayer Leverkusen in the 2023/24 Bundesliga

## Quick start

```bash
make setup
make test
make build-cases
make demo
```

Open the local URL printed by Streamlit. Raw event files are downloaded from the official source into `data/cache/` and are not committed.

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
- `src/signalroom/evidence.py`: event trace construction
- `src/signalroom/reporting.py`: deterministic narrative and grounding checks
- `app.py`: analyst interface
- `artifacts/cases/`: reproducible derived case outputs, no raw event dataset
- `docs/`: product, data, analytics, evaluation, architecture, and decision records
- `outreach/`: stakeholder-ready material

## Honest positioning

SignalRoom supports teams and competitions available through its implemented event-data adapters. The initial version uses StatsBomb Open Data and is designed so additional providers can be added later.

This repository is not affiliated with or endorsed by Brighton & Hove Albion, Bayer Leverkusen, StatsBomb, Hudl, or any other club or data provider. The case studies are historical and are not current tactical advice.

## Data terms and attribution

The source data is [StatsBomb Open Data](https://github.com/hudl/open-data). Its README requires StatsBomb attribution and use of its logo when publishing analysis. The data remains subject to the [StatsBomb Public Data User Agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf). SignalRoom does not redistribute the raw dataset.

The repository's MIT license applies to SignalRoom's original source code only. It does not relicense StatsBomb data or branding.


