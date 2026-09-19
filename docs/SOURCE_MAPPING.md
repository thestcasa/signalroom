# StatsBomb source mapping

| Internal field | StatsBomb field | Public artifact treatment |
| --- | --- | --- |
| event ID | `id` | Internal only |
| match ID | file and match manifest | Retained for historical context |
| player and team IDs | `player.id`, `team.id` | Namespaced internally |
| recipient | `pass.recipient` | Derived role summary |
| body part | action-specific `body_part` | Derived summary |
| delivery height | `pass.height` | Derived summary |
| technique | action-specific `technique` | Derived summary |
| outcome | action-specific `outcome` | Derived summary |
| source coordinates | `location`, action `end_location` | Cache only |
| canonical coordinates | selected-team transform | Internal; public lane only |
| possession | `possession` | Boundary logic, not published as a football phase |
| linked events | `related_events` | Internal only |
| shot xG | `shot.statsbomb_xg` | Aggregated or derived summary |
| lineup exposure | lineup position intervals | Derived player exposure table |

