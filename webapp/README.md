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
