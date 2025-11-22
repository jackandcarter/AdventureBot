# AdventureBot Web App

This service ports the Discord AdventureBot experience to a standalone web stack. It is written in TypeScript, runs on Node.js 18+, and targets MariaDB for persistence.

## Project layout
- `src/config`: Environment loading and validation.
- `src/logger.ts`: Shared pino logger setup.
- `src/db`: Database pool and readiness checks.
- `src/routes`: HTTP route handlers (health/readiness and lobby APIs).
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

## Lobby endpoints (in-memory prototype)
- `GET /api/lobbies` – list public lobbies and their player counts.
- `POST /api/lobbies` – create a lobby. Body: `{ ownerId: string, name?: string, visibility?: "public" | "private" | "invite", maxPlayers?: number }`
- `GET /api/lobbies/:lobbyId` – fetch lobby details including players/ready states.
- `POST /api/lobbies/:lobbyId/join` – join a lobby. Body: `{ playerId: string, displayName?: string }`
- `POST /api/lobbies/:lobbyId/leave` – leave a lobby. Body: `{ playerId: string }`
- `POST /api/lobbies/:lobbyId/ready` – toggle ready status. Body: `{ playerId: string, ready: boolean }`
- `POST /api/lobbies/:lobbyId/start` – request start (owner only; requires all players ready). Body: `{ playerId: string }`

The current implementation keeps lobby state in-memory to flesh out the API surface. Persistence, authentication, invite/code validation, and WebSocket updates will be layered in subsequent iterations per the roadmap.
