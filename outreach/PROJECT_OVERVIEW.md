# SignalRoom: project overview

SignalRoom is a club-independent football intelligence prototype that converts event data into short, evidence-linked historical briefings. It was built to demonstrate an end-to-end applied AI and data-engineering workflow: source ingestion, provider normalization, metric design, statistical validation, uncertainty-aware finding selection, event traceability, and analyst-facing presentation.

The first version uses StatsBomb Open Data. A configuration selects the competition, season, and team. No analytical rule contains club-specific logic.

The central design choice is abstention. SignalRoom is allowed to publish no broad tactical-change finding when the sample, magnitude, stability, or evidence is weak. SetPieceLab provides a deeper bounded view of attacking corner routines with source event sequences and sample warnings.

This is an independent historical case study. It is not affiliated with a club, does not use private club data, and does not claim to replace professional internal systems.

