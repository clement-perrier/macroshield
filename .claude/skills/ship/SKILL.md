---
name: ship
description: Run whichever test suite(s) are in scope for the current changes, commit with a conventional-commit message, and push to origin.
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(uv *) Bash(cd *) Bash(grep *) Bash(npm *)
---

# Ship: test, commit, push

Monorepo layout: `backend/` = Python/FastAPI (tests via `uv run pytest`),
`frontend/` = Next.js/TS (no test script defined yet as of 2026-08 — check
before assuming one exists).

Current status:
!`git status --short`

Changed paths (staged + unstaged) vs HEAD:
!`git diff HEAD --name-only`

## Steps

1. **Determine scope** from the changed paths above.
   - Nothing under `backend/` changed → skip backend tests.
   - Nothing under `frontend/` changed → skip frontend tests.
   - Only `docs/`, root `README.md`, or root `CLAUDE.md` changed → skip
     tests entirely.

2. **Run the tests that are in scope:**
   - Backend: `cd backend && uv run pytest`
   - Frontend: first check `grep '"test"' frontend/package.json` — there is
     no `test` script as of this writing, so if it's still absent, skip and
     say so rather than running `npm test` and hitting "missing script".

   If anything in scope fails, **stop here** — report the failure, do not
   commit or push.

3. **Stage and commit.**
   - Check `git status` for anything unexpected (stray files, anything that
     might be a secret) before staging — don't blindly `git add -A`/`git
     add .`; stage the specific files that make up this change.
   - Write a conventional-commit message (`feat:`, `fix:`, `chore:`,
     `docs:`, …) describing *why*, matching this repo's existing style
     (`git log --oneline -10`).
   - No need to manually strip a `Co-Authored-By: Claude` trailer — this
     repo's `.claude/settings.json` sets `attribution.commit: ""`, so
     Claude Code doesn't add one here.

4. **Push:** `git push`. If there's no upstream yet, `git push -u origin HEAD`.

5. **Report back** in 2-3 sentences: which test suite(s) ran and their
   result, what was committed, and confirmation it pushed. Don't dump a
   full diff.

If `git status --short` is empty, say so and stop — there's nothing to ship.
