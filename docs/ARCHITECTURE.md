# Architecture

SignalRoom remains a batch-oriented, file-based historical workbench.

```text
pinned source + rights manifest
  -> provider adapter and local cache
  -> match, event, lineup and coordinate contracts
  -> restart observations with explicit boundaries
  -> complete-population and selected-team analyses
  -> rights-safe evidence summaries
  -> validated JSON, CSV, HTML and quality reports
  -> Streamlit review and state-matched export
```

## Public historical mode

The checked-in and deployed artifacts contain only permitted analysis, derived summaries, provenance, attribution, and explicit limitations. Raw provider files remain ignored. Build gates reject forbidden public fields.

## Private evaluation target

A future private mode may accept authorized club or provider data with access, retention, deletion, export, and training controls. No private mode or commercial deployment is claimed in this milestone.

## Deliberate simplicity

The project does not include streaming ingestion, a feature store, a model registry, multi-tenancy, generalized provider adapters, custom computer vision, or an LLM layer.
