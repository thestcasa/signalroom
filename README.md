# SignalRoom

SignalRoom is a historical set-piece evidence workbench. It helps an analyst inspect recorded attacking dead-ball delivery tendencies, compare declared match windows, review derived evidence summaries, and export a cautious briefing.

**Live demo:** https://signalroom-tka1.onrender.com

It is an applied analytics case study by Alessandro Casadei. It is not a club-ready opposition-intelligence product, a routine detector, a source of defensive recommendations, or an externally validated workflow.

## Implemented scope

- Attacking corners
- Wide final-third free-kick passes
- Central final-third free-kick passes, with legal direct or indirect status explicitly unavailable
- Direct free-kick shots, reported without tautological shot-conversion percentages
- Explicit sequence termination and censoring
- Recorded roles for taker, intended recipient, first post-delivery actor, and shot actor
- Match-block uncertainty for recent-versus-preceding corner delivery-group shares
- Complete FA Women's Super League 2023/24 coverage: 132 fixtures and 12 teams
- Leave-Brighton-out descriptive peer context
- Bayer Leverkusen historical case with league peer comparison suppressed because the release is not a complete Bundesliga population
- Rights-safe public artifacts containing aggregates and derived evidence summaries, not raw records or source event IDs

The application uses one analysis context across the shortlist, evidence review, and HTML export. Every displayed evidence reference resolves to an included derived summary.

## Data and rights

The source is [StatsBomb Open Data](https://github.com/hudl/open-data), pinned to revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.

The source agreement permits public analysis with attribution but prohibits redistributing or reproducing the underlying data. SignalRoom therefore blocks raw records, source event IDs, exact source excerpts, and exact source-coordinate timelines from public bundles. Public artifacts contain attributed aggregates and SignalRoom-derived summaries. Commercial use remains blocked without written permission.

The repository MIT licence applies only to original SignalRoom code. It does not relicense provider data or branding.

## Quick start

```bash
make setup
make test
make build-cases
make demo
```

Raw source files are downloaded into ignored cache paths. Generated case bundles, coverage reports, evidence-integrity reports, and manual-review samples are stored under `artifacts/cases/`.

## Verification

```bash
make lint
make test
make build-cases
```

The milestone regression report is in `audit/MILESTONE_REGRESSION.md`. It maps F01 to F24 to implementation and verification evidence.

## Repository map

- `src/signalroom/adapters/`: pinned provider ingestion, lineups, and source-field preservation
- `src/signalroom/coordinates.py`: selected-team coordinate frame
- `src/signalroom/deadballs.py`: restart and bounded sequence contract
- `src/signalroom/setpieces.py`: recorded corner delivery groups
- `src/signalroom/opponent.py`: match-block comparison and review gates
- `src/signalroom/peer.py`: complete-population descriptive peer baseline
- `src/signalroom/evidence.py`: internal reference validation and public derived evidence
- `src/signalroom/rights.py`: machine-readable publication gates
- `src/signalroom/pipeline.py`: deterministic case builds and quality reports
- `app.py`: historical review interface
- `manifests/`: source and rights declarations
- `docs/`: current analytical, product, and validation contracts
- `audit/`: regression status, residual risks, and readiness decision

## Deployment

`render.yaml` defines one free-plan Streamlit web service with no secrets or external infrastructure. The health endpoint is `/_stcore/health`. Free services may cold-start after inactivity.

## Honest limitations

Event data does not provide continuous off-ball movement, screens, marking assignments, tactical intent, or synchronized video. Historical open data is not current preparation data. The public workflow has not been tested by independent professional analysts, so no external validation or adoption is claimed.
