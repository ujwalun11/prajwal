# Three-person Git workflow

## Branches

| Contributor | Branch | Owns |
|---|---|---|
| Person A | a/engine | backend/app/events, sync, trust, tasks, priority, allocation; main.py; requirements |
| Person B | b/field | web/field |
| Person C | c/command | backend/app/routing, insights, simulate; web/dashboard; scenario; scripts |

## Rules

1. Keep main as the shared integration branch. Do not commit feature code directly to main.
2. Each contributor pulls main, checks out their feature branch and commits only their owned paths.
3. Use small, coherent commits: type(scope): summary. Never force-push.
4. Open a PR from the feature branch to main. Describe scope, tests, screenshots where useful, and decisions/TODOs.
5. The team lead reviews and merges each PR. Do not merge PRs automatically.
6. Before a checkpoint, fetch main into the feature branch and run the contributor's tests plus the integration smoke test.
7. If a conflict is in another person's owned file, stop and coordinate; do not resolve their implementation unilaterally.
8. Shared settings sections: SHARED requires team agreement; Person A owns SECTION A; Person C owns SECTION C.
9. Never modify /contracts without explicit team agreement. Treat source contract artefacts as frozen.
10. Never commit .env files, local SQLite DBs, photos, IndexedDB dumps, node_modules, dist, local PMTiles, or certificates.

## Commands

```powershell
git clone https://github.com/ujwalun11/prajwal.git
cd prajwal
git pull origin main
git switch a/engine   # use b/field or c/command for the assigned role
git pull origin main
git status --short --branch
```

Commit and push:

```powershell
git add <owned-paths>
git commit -m "feat(engine): implement event sync"
git push -u origin a/engine
```

Open a PR to main. To showcase a teammate's work without merging, clone the repository and run:

```powershell
git fetch origin
git switch --track origin/b/field
```

Likewise for a/engine and c/command.
