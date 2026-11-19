# Contributing

Read docs/team-workflow.md before changing code. Select the correct feature branch and stay within the owner's paths. Keep contracts immutable.

All decision logic must be deterministic and accompanied by plain-language reasons. New demo assumptions belong in backend/app/settings.py. Add tests for each meaningful engine or API change. Frontends must write locally first, display sync status, and label stale/offline data with an as-of time.

Do not describe simulated results as real emergency data. TRANA is a hackathon prototype and not certified for live disaster operations.
