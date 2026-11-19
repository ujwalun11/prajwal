# Agreed decisions (TRANA)

All numbers are DEMO ASSUMPTIONS, set in ONE settings file (backend/app/settings.py). Never hard-code them elsewhere.

## Decisions 1-14 (agreed by the team)
1. **Demo time.** All times are in scenario minutes, converted with one constant `SCENARIO_MINUTE_SECONDS` (60 for a 10-minute run, 20 for a 3-minute demo). Replay stamps events with the send time.
2. **Volunteer location.** Volunteer phones send a `volunteer_location` event (envelope `location`) at each sync. A location older than 15 scenario minutes counts as unknown.
3. **Nearest volunteer.** Straight-line distance from the last usable location. If none, the task stays `unassigned` and the dashboard shows a warning.
4. **Join codes.** Codes (e.g. CAMP-A1, VOL-01, COORD-01) live in the backend settings file. `POST /api/join` returns role, user_id, camp_id. Not real security.
5. **Verification outcomes.** `confirmed`: confidence of that camp's latest facts rises. `differs`: the volunteer's numbers are added as NEW events (never overwrite); `unreachable`: camp stays uncertain and the coordinator is alerted.
6. **Uncertain camps in allocation.** They get the same 1-day minimum guarantee, marked `provisional`, plus a verification task.
7. **Scoring and trust values.** See the table below.
8. **Units.** Water and food in person-days, medicine in kits, blankets in pieces.
9. **Vehicles.** Informational only (route and ETA display). No capacity planning.
10. **Stale plans.** Approving a plan whose inputs changed returns 409 `plan_out_of_date`; the dashboard refreshes.
11. **Deliveries.** Approval writes one `delivery_update` (assigned) per allocation line. A "mark delivered" button on the dashboard sends delivered events.
12. **Privacy.** Aggregated counts only (elderly, children, medical). No individual records. No faces in demo photos.
13. **Equity metrics (Trana vs a request-count baseline).** (a) share of override and high-tier camps that get the minimum guarantee; (b) days of supply at the worst-served camp; (c) allocated/need per camp: lowest value and spread.
14. **Languages.** English first. Hand-written Kannada and Hindi label files only after the hour-14 gate.

## Scoring defaults (demo assumptions)
| Setting | Value |
|---|---|
| Source trust | verification report 1.0, camp lead 0.8, volunteer observation 0.8, simulated sensor 0.7, citizen 0.5 |
| Freshness half-life (scenario minutes) | road status 4, water level 3, camp status 8, stock report 8, shortage request 6 |
| Corroboration | second agreeing source x1.2 (cap 1.0); conflicting report x0.5 |
| Confidence bands | >= 0.70 confirmed; 0.40-0.69 unconfirmed; < 0.40 uncertain |
| Expected report interval | 2 min; flagged uncertain after 1.5x (3 min) |
| Allocation | target 3 days of supply; minimum guarantee 1 day |
| Daily need per person | water 15 L (check the current Sphere Handbook), food 1 ration (simplified); medicine by request |
| Tier 1 (override) | confirmed medical emergency, or less than 1 day of drinking water |
| Score weights | days-of-supply shortfall 0.40, vulnerable share 0.25, time since last delivery 0.20, access difficulty 0.15 |
| Tier cut-offs | High >= 60, Medium 30-59, Low < 30 |
| Task timeouts | accept within 3 min else escalate to next nearest; complete within 10 min |

## Contract-level decisions 15-21
15. **Site registration.** Camps and depots are registered with `site_registered` events (the replay sends them first). No admin endpoint.
16. **Tasks work offline.** Accepting and reporting a task are EVENTS (`task_accepted`, `verification_report`) sent through the outbox and `/api/sync`. The REST endpoints `POST /api/tasks/{id}/accept` and `/report` from the first brief are REMOVED.
17. **Task delivery.** `POST /api/sync` returns the user's open `tasks`. `GET /api/tasks` also exists (dashboard).
18. **Photos.** Events carry `photo_ref` (UUID). The photo is uploaded separately with `PUT /api/photos/{photo_id}` (idempotent) and read with `GET`. Text events sync first, photos after. Stored in `backend/data/photos/` (git-ignored).
19. **State endpoints.** `GET /api/state/camps`, `/depots`, `/roads`, `/events`. `state_version` changes only when plan-relevant inputs change. Event `seq` and the sync `cursor` order arrivals.
20. **Dashboard actions are events.** "Mark delivered" and similar actions are sent through `POST /api/sync` (device_id "dashboard").
21. **Roads and sectors.** `road_id` and `sector_id` values must exist in `/scenario/roads.geojson`; Person C owns that file and tells A and B the IDs.

## Clarifications 22-26
22. **Event subject by type.** Where a payload repeats an ID (road_id, sector_id, camp_id, task_id, plan_id, allocation_id), it MUST equal the subject. `site_registered` uses the new camp/depot ID; camp_status, shortage_request and verification_report use camp_id; stock_report uses a camp or depot ID; road_status uses road_id; water_level, landslide_risk and team_dispatch use sector_id; task_accepted uses task_id; delivery_update uses allocation_id; decision uses plan_id; volunteer_location uses author_id.
23. **Severity** is for display and sorting only; no engine uses it for decisions. `shortage_request`: critical if urgency is critical or medical_flag is true; warning if urgency is high; otherwise info. `verification_report`: critical if differs and observed water is below 1 day, otherwise warning for differs or unreachable and info for confirmed. Other types are info except blocked/flooded road_status, chest-or-higher water_level, and high landslide_risk, which are warning.
24. **ID list.** Person C publishes `/scenario/ids.json` with camp, depot, road and sector IDs. Person A shares the join-code list in backend settings with B and C.
25. **Joining needs the network once.** `POST /api/join` is validated by the server, so each phone must join while it can reach the backend. After that the session stays on the phone and everything works offline.
26. **Dashboard identity.** The dashboard joins once with COORD-01 to obtain its user_id, uses it as author_id and approved_by, and uses sync device_id "dashboard". Volunteer positions are read from latest `volunteer_location` events in `GET /api/state/events`.
