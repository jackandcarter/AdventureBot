# AdventureBot Web App

This service ports the Discord AdventureBot experience to a standalone web stack. It is written in TypeScript, runs on Node.js 18+, and targets MariaDB for persistence.

## Project layout
- `src/config`: Environment loading and validation.
- `src/logger.ts`: Shared pino logger setup.
- `src/db`: Database pool and readiness checks.
- `src/routes`: HTTP route handlers (currently health and readiness checks).
- `src/app.ts`: Express app wiring.
- `src/server.ts`: Server bootstrap that binds the HTTP port.

## Getting started
1. Copy the environment template and fill in database credentials:
   ```bash
   cd webapp
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create or refresh the database schema and seed data from the repository dump:
   ```bash
   npm run db:setup
   ```
   This script creates the configured database if it does not exist, then installs the AdventureBot tables and seed rows from
   `database/dump.sql`.

4. Run the development server with automatic reloads:
   ```bash
   npm run dev
   ```
5. Build the production bundle:
   ```bash
   npm run build
   ```
6. Start the compiled server:
   ```bash
   npm start
   ```

## Health endpoints
- `GET /health` returns an immediate OK payload to verify the process is running.
- `GET /ready` performs a lightweight database ping against the configured MariaDB instance.

## In-browser lobby prototype
You can now try the lobby and session flows directly from the server without extra tooling. Start the dev server (`npm run dev` from `webapp/`) and open [http://localhost:3000](http://localhost:3000) to load a static UI that exercises the APIs:

- Create new lobbies with difficulty, join rules, optional passwords, and max player counts.
- Difficulty options are loaded from the database seed values (Easy, Medium, Hard, Crazy Catto) instead of hard-coded lists.
- View the list of active rooms, copy session IDs, and prefill the join inspector.
- Post lobby chat messages (optionally tagged to a session) and see the chat feed update.
- Join rooms, then load a session to inspect players, recent log entries, and grid size.

## Game session prototype APIs
Early web game APIs are exposed under `/api` and use in-memory state to start experimenting with browser gameplay flows:

- `GET /api/difficulties` — surface the difficulty definitions mirrored from the database (Easy, Medium, Hard, Crazy Catto) with floor sizing, enemy chances, and basement tuning.
- `POST /api/sessions` — create a new dungeon run with an owner name and optional difficulty (`easy`, `medium`, `hard`, `crazy_catto`). Returns the session ID and owner player ID.
- `POST /api/sessions/:sessionId/join` — join an existing run by session ID and player name. Responds with the joining player ID plus the updated session state.
- `GET /api/sessions/:sessionId` — fetch the latest session state (players, turn order, log, and grid size).
- `POST /api/sessions/:sessionId/actions/move` — move the active player north/south/east/west. Enforces turn order and appends a descriptive log entry for the discovered room type.

Sessions now support lobby-style controls: optional passwords, configurable maximum party size, and a toggle that allows or blocks mid-dungeon joins once a run begins. Live sessions report their status (`waiting` or `in_progress`), whether a password is required, and how many seats remain.

## Hub content APIs
Hub/tutorial surfaces now pull directly from the `hub_embeds` and `high_scores` tables so the web UI can mirror the Discord experience:

- `GET /api/hub/main` — returns the primary hub embed row (title, description, hero image, and news text field) or `null` when not configured.
- `GET /api/hub/tutorial?page=1` — fetches a tutorial page by 1-based index, reporting the total page count so clients can paginate.
- `GET /api/hub/high-scores?sort=score_value&limit=20` — retrieve leaderboard entries sorted by score, enemies defeated, bosses defeated, gil, level, or rooms visited (defaults to score).

## Lobby and cyber chat prototype APIs
The lobby surfaces an in-memory chat feed alongside the list of joinable rooms to help players coordinate:

- `GET /api/lobby` — fetch the current lobby snapshot (chat messages annotated with session summaries and the live room list).
- `POST /api/lobby/messages` — append a chat message with an author and body; optionally associate it with a session ID so UI can deep-link into a lobby entry.
- `POST /api/lobby/rooms` — create a new room with difficulty, allow-join toggle, optional password, and max player count. The response returns the initial session state plus an updated lobby snapshot so the UI can refresh the chat feed and room list.

Sessions currently live only in memory to keep iteration fast; they will be backed by MariaDB and real game logic in future phases.
