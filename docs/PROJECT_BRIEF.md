# Project brief

## Problem

Event-data dashboards expose many numbers but leave analysts to decide what changed, whether it is reliable, and which events support the interpretation.

## Product

SignalRoom selects a target team through configuration, compares a non-overlapping recent match window with its preceding baseline, suppresses weak changes, and links published findings to event sequences. SetPieceLab applies the same evidence model to attacking corners.

## Audience and job

The primary user is a football analyst preparing an initial opposition or retrospective review. The product helps the analyst triage what deserves video or deeper contextual review. It does not replace video, coaching judgment, or private tracking data.

## Delivery decision

Build a narrow SignalRoom MVP with SetPieceLab as its most complete module. Brighton Women 2023/24 provides 22 matches and 92 attacking corners, enough for a historical example. Broad changes are published only when gates pass. Bayer Leverkusen 2023/24 is the portability validation.

