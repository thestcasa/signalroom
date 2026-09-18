# Data-source research and legal boundary

Reviewed 18 September 2026. SignalRoom uses only legitimate, attributable source packages and does not scrape websites, acquire paid feeds, or redistribute raw provider data.

| Source | Data observed | Set-piece relevance | Off-ball / identity | Use decision |
| --- | --- | --- | --- | --- |
| [StatsBomb Open Data](https://github.com/hudl/open-data) | Competitions, matches, event files, lineups, selected 360 | Event restart labels, locations, players, shots, xG; selected 360 can add positions | Event player identities; 360 positions where released | Implemented through a pinned adapter. Governed by the repository README and [public-data agreement](https://github.com/hudl/open-data/blob/master/LICENSE.pdf); attribution retained. |
| [Metrica Sports sample data](https://github.com/metrica-sports/sample-data) | Anonymized event and synchronized tracking samples | Useful for future event-to-tracking contract tests | Tracking positions, anonymized identities | Conceptual future adapter only. Sample coverage is small and redistribution follows the repository terms. |
| [SkillCorner Open Data](https://github.com/SkillCorner/opendata) | Public sample tracking, dynamic events, phases, and body pose for selected matches | Strong future movement and shape source | Tracking and pose, limited sample | Conceptual future adapter only. No current case is built from it. |
| [SoccerNet data](https://www.soccer-net.org/data) | Research datasets for tracking, action spotting, calibration, and video tasks | Useful for research benchmarks and video capability planning | Varies by dataset; video access can be gated | Conceptual research source. No gated video or NDA material is used. |
| Hudl StatsBomb, Opta / Stats Perform, Wyscout, SkillCorner commercial | Professional event, video, and tracking products | Future licensed adapters | Provider-specific | Commercial opportunity only. No paid data is acquired or implied. |

## Capability contract

SignalRoom labels every current finding `Level 1 · event data`. This supports restart classification, delivery and first-contact locations where recorded, shot and xG outcomes, second-phase recorded events, and player involvement. It cannot verify screens, decoy runs, marking structure, off-ball timing, or video clips.

Level 2 adapters may add 360 or tracking positions. Level 3 requires a legitimate synchronized video package. A source being publicly described does not make an unavailable video link or an unlicensed copy acceptable.

## Coverage decision

The fully implemented domain is attacking final-third dead balls: corners, wide attacking free kicks, indirect attacking free kicks near the penalty area, and direct free-kick shots. Attacking throw-ins, goal kicks, kick-offs, penalties, defensive restarts, and richer second-phase interpretation are reserved for the same provider-neutral contract, but are not presented as implemented. Competition prevalence is suppressed when complete comparable coverage is not loaded.
