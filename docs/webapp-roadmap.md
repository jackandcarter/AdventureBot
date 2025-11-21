# AdventureBot Web App Roadmap

A task-oriented roadmap for creating the standalone browser-based AdventureBot service (Node + MariaDB) that mirrors the Discord game’s logic while delivering a lobby-driven web experience. The web app is a separate service that can reuse existing database helpers/contexts as references but will implement its own backend and auth stack.

## Phase 0 – Project scaffolding
- Create a new top-level `webapp/` service directory with separate package.json and env templates for native Ubuntu 24 + MariaDB (no Docker).
- Establish tooling: Node LTS version, package manager, ESLint/Prettier, test runner (e.g., Vitest/Jest), and commit hooks.
- Define shared library boundaries for reusing game logic (e.g., `packages/game-logic`) vs. web-specific services.
- Add documentation for local dev (setup MariaDB, seed data, run web server + watcher).

## Phase 1 – Core backend skeleton
- Stand up an HTTP API server (Express/Fastify) with health/readiness endpoints and structured logging.
- Implement config management (env schema validation) and secrets handling.
- Add database client layer reusing patterns from existing helpers (connection pool, migrations, transactions).
- Wire migration tool and initial migration baseline (existing adventure data + placeholders for auth/lobbies).

## Phase 2 – Auth and identity
- Design user model (email/password) with salted hashing, verification tokens, and session tokens (httpOnly cookies + CSRF or JWT with rotation).
- Build signup + email verification flows (rate limits, token expiry, resend rules).
- Implement login/logout, password reset, and basic profile endpoints.
- Add audit logging for auth events and brute-force protection (IP/email throttling, optional CAPTCHA hook).

## Phase 3 – Email delivery
- Choose provider (SMTP/SES/SendGrid) and SDK abstraction.
- Create templates for verification, invites, and password reset; store them in-versioned files.
- Implement tokenized links with expiry and single-use semantics.
- Add background job/queue or lightweight scheduler for retries and bounce handling.

## Phase 4 – Lobby and matchmaking
- Design lobby schema (max 6 players, status, owner, invite tokens, visibility: open/invite/code-based).
- Build lobby CRUD APIs: create, list/discover, join via invite/code, ready-check, start game, leave/timeout cleanup.
- Implement real-time channel (WebSockets/SSE) for lobby presence, chat, ready state, and start signal.
- Add rate limits and lifecycle rules (idle timeout, max concurrent lobbies per user).

## Phase 5 – Game session service
- Port game logic from the Discord version into web-oriented services that preserve behaviors (procedural dungeon generation, encounters, items, locked doors/chests/hidden rooms/mini-bosses/staircases).
- Define deterministic seed handling and persistence for turn-based state per session.
- Implement turn engine APIs: create session from lobby, fetch state, submit player actions, resolve turn, advance round, and handle end-of-run scoring.
- Add concurrency control and optimistic locking to prevent double-turn submissions; include reconnection flow for dropped clients.

## Phase 6 – Gameplay event bus and notifications
- Standardize event schema for game/lobby updates (player joined, action resolved, loot awarded, boss spawned, run completed).
- Bridge event bus to WebSockets for real-time UI updates; persist key events for replay/logging.
- Add server-side validation and anti-cheat checks for action payloads.

## Phase 7 – Web UI/UX
- Scaffolding: choose React/Next.js or similar; set up routing, global state (e.g., Redux/RTK Query or TanStack Query), theming, and localization hooks.
- Screens: landing page, auth (signup/login/verification), lobby list/discover, lobby detail (live join list + ready), game session view (turn log, map/room info, action controls), profile/settings.
- Interaction patterns: command palette or action buttons mirroring Discord commands; notifications/toasts; keyboard shortcuts.
- Accessibility and responsiveness: ARIA labels, focus management, mobile-friendly layouts; cross-browser support targets.

## Phase 8 – Shared data and migrations
- Finalize database migrations for auth, lobbies, game sessions, inventory/loot, and audit trails while coexisting with existing tables.
- Seed data for testing (sample users, lobbies, starter items) and fixtures for automated tests.
- Establish backup/restore scripts and data retention policies.

## Phase 9 – Observability, ops, and security hardening
- Metrics/logging/tracing stack (e.g., OpenTelemetry + chosen collector) with dashboards for latency, errors, lobby counts, game throughput.
- Health/readiness probes, rate limiting (per-IP/per-account), and abuse monitoring.
- Secrets management strategy and key rotation; HTTPS/TLS termination expectations.
- Privacy: data export/delete hooks if required; PII redaction in logs.

## Phase 10 – Testing and QA
- Unit tests for services (auth, lobby, game logic), integration tests for API/database, and contract tests for real-time channels.
- End-to-end tests for core flows: signup/verify, create lobby, invite/join, ready/start, play turns, end game.
- Load testing for lobby churn and turn resolution concurrency; chaos testing for dropped connections.
- Add CI pipeline (lint/test/build) and artifacts (coverage, reports); plan staging environment deployment.

## Phase 11 – Launch readiness
- Finalize production build configs and native deployment steps (e.g., systemd/PM2 scripts) without containerization.
- Security review and dependency audit; lock versions.
- Run beta with monitored feature flags; collect telemetry/feedback and iterate.

## Suggested execution order
Follow phases in order; within each phase, complete dependencies first (e.g., database + auth before lobby/game UI). Iterate with small PRs per phase to keep changes reviewable.
