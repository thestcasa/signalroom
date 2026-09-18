# Decision record

## D001: Narrow flagship, deep specialist module

Selected a narrow SignalRoom MVP with SetPieceLab as the most complete module. Brighton has sufficient set-piece volume, while only a subset of broad metrics may survive small-window uncertainty. A system that abstains is more credible than a full but weak briefing.

## D002: No LLM in v1

The deterministic template already produces readable grounded output. An LLM would add validation burden without improving the core feasibility claim.

## D003: File-based bundles instead of a database

Two historical cases and tens of matches do not justify operational infrastructure. JSON, CSV, PNG, and HTML outputs improve auditability and fresh-clone reproducibility.

## D004: Match-level resampling

Events within a match are dependent. The match is the resampling unit. Results remain schedule-conditional and are not causal.

## D005: Do not commit raw data

Acquisition is reproducible and cache-first. Raw provider records remain ignored to reduce repository size and respect source-data controls.

## D006: Neutral branding

SignalRoom uses its own ink, teal, coral, and paper palette. Club branding and colors are excluded. The official StatsBomb logo is used only for required data attribution.

