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
3. Run the development server with automatic reloads:
   ```bash
   npm run dev
   ```
4. Build the production bundle:
   ```bash
   npm run build
   ```
5. Start the compiled server:
   ```bash
   npm start
   ```

## Health endpoints
- `GET /health` returns an immediate OK payload to verify the process is running.
- `GET /ready` performs a lightweight database ping against the configured MariaDB instance.

## Game session prototype
Early web game APIs are exposed under `/api` and use in-memory state to start experimenting with browser gameplay flows:

- `POST /api/sessions` — create a new dungeon run with an owner name and optional difficulty (`easy`, `normal`, `hard`). Returns the session ID and owner player ID.
- `POST /api/sessions/:sessionId/join` — join an existing run by session ID and player name. Responds with the joining player ID plus the updated session state.
- `GET /api/sessions/:sessionId` — fetch the latest session state (players, turn order, log, and grid size).
- `POST /api/sessions/:sessionId/actions/move` — move the active player north/south/east/west. Enforces turn order and appends a descriptive log entry for the discovered room type.

Sessions currently live only in memory to keep iteration fast; they will be backed by MariaDB and real game logic in future phases.
