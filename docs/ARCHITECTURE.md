# Architecture

```mermaid
flowchart TD
    A[StatsBomb adapter] --> B[Internal events]
    B --> C[Validated transformations]
    C --> D[Versioned metrics]
    C --> E[Dead-ball sequences]
    D --> F[Statistical gates]
    E --> G[Routine groups]
    F --> H[Evidence builder]
    G --> H
    H --> I[Grounded bundle]
    I --> J[Streamlit interface]
    I --> K[HTML and PDF outputs]
```

The MVP is a local Python application. It has no database, queue, authentication layer, external LLM, or hosted dependency. Raw acquisition is cache-first. Derived evidence bundles are portable and reviewable without redistributing raw provider files.

Provider-specific parsing stops at the adapter. Metrics, gates, evidence construction, reporting, and presentation consume internal models.

The provider-neutral `DeadBallSequence` contract carries restart type, delivery, first recorded contact, second phase, shots/xG, participants, data quality, source revision, evidence IDs, and a capability level. The current complete domain is attacking final-third dead balls. The same contract is reserved for throw-ins, goal kicks, kick-offs, penalties, defensive restarts, tracking fields, and synchronized video references.

`capabilities.py` is the publication registry. Current outputs are Level 1 event data. Level 2 360/tracking and Level 3 synchronized video are explicitly adapter-ready or unavailable, never silently inferred.

The opponent-preparation layer (`opponent.py`) consumes typed evidence sequences rather than provider records. It owns routine-family grouping, window denominators, uncertainty, quality gates, and stability labels. The Streamlit app only selects state and renders the resulting structured comparisons. The HTML briefing uses the same structured values and evidence IDs, so it cannot silently diverge from the interface.
