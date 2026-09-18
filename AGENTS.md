# Agent operating guide

## Product invariants

- Never add a finding that is not computed and evidence-linked.
- Never weaken sample, stability, or grounding gates to make a report look fuller.
- Keep club names and IDs in configuration or derived bundles, never analytical logic.
- Raw provider records belong under ignored cache paths.
- Synthetic records are allowed only in tests.
- The application must work without an LLM or API key.
- Historical cases must remain labeled as historical.

## Change workflow

1. Read the relevant specification in `docs/`.
2. Add or update tests with analytical changes.
3. Run `make lint`, `make test`, and the affected real-data case build.
4. Validate every evidence reference and generated narrative.
5. Update the claims ledger and screenshots if stakeholder output changes.

## Definition of done

A change is done only when unit tests, a real-data workflow, and output grounding checks pass. Code existence alone is not enough.

