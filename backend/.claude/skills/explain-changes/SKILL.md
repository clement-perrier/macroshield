---
name: explain-changes
description: After making a non-trivial change to the Python/FastAPI backend (new files, new dependencies, schema/migration changes, a new architectural piece — not one-line fixes or formatting), explain what was built in plain language for someone whose primary stack is Java/Spring Boot, not Python. Trigger whenever wrapping up backend work that touches more than a couple of files or introduces a new library/pattern.
---

# Explain backend changes

The user's primary stack is Spring Boot (Java) + React Native, not Python — this
backend (FastAPI/SQLAlchemy/etc.) is the part of their stack they're least
familiar with (see `backend/CLAUDE.md`: "Python is not my specialty, don't
hesitate to explain lines of code"). After finishing a non-trivial change here,
don't just report file names — walk through it so it actually makes sense to a
Java-background engineer.

## When to use this

Use after: adding a new module/service, adding a dependency, touching
migrations/schema, introducing a new library or pattern (async, DI, ORM,
scheduler, etc.), or any multi-file change.

Skip for: single-line fixes, renames, formatting-only diffs, config tweaks with
no new concept involved.

## How to explain

1. **Lead with the "why"** in one or two sentences — the problem this solves —
   before any code detail.
2. **Go file by file** (or logical group of files), each in a couple of
   sentences: what it does and why it exists, not just what's in it.
3. **Name new concepts/libraries the moment they first appear**, one line each.
   Prefer a **Java/Spring analogy** over a from-scratch definition, e.g.:
   - `async def` / `await` — non-blocking, but cooperative rather than
     thread-per-request; roughly Java's `CompletableFuture` chains but with
     sequential-looking syntax.
   - FastAPI `Depends(...)` — dependency injection, like `@Autowired` /
     constructor injection.
   - SQLAlchemy ORM (`Mapped[...]`, `mapped_column`) — like JPA/Hibernate
     `@Entity` / `@Column`.
   - Alembic — like Flyway/Liquibase: versioned migration scripts with
     `upgrade()` / `downgrade()`.
   - APScheduler `CronTrigger` — like Spring's `@Scheduled(cron = ...)` or
     Quartz.
   - `@lru_cache` on a factory function — cheap singleton, like a Spring
     `@Bean` with default (singleton) scope.
   - `async with` (context manager) — like try-with-resources: guarantees
     cleanup even on error.
   - Pydantic models — DTOs with validation, like classes annotated with Bean
     Validation.
4. **Don't explain what's obvious from a Java background** (classes,
   functions, imports) — focus on what's Python/async/FastAPI-idiomatic and
   would actually trip someone up.
5. **End with what's runnable/testable now**, and anything still manual (env
   vars to set, infra not yet provisioned, etc.) — not a generic "let me know
   if you have questions."

Keep it a prose walkthrough, not a wall of bullets — bullets are fine for the
concept call-outs, but the file-by-file part should read like an explanation,
not a changelog.
