# Architecture

```mermaid
flowchart TD
    A[StatsBomb adapter] --> B[Internal events]
    B --> C[Validated transformations]
    C --> D[Versioned metrics]
    C --> E[Corner sequences]
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

