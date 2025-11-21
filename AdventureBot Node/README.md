# AdventureBot Node

Browser-first web experience for AdventureBot using Node.js/Express and MariaDB/MySQL. The goal is to mirror the game systems used by the Discord bot while providing account-based access, email verification, and a lobby for launching browser sessions.

## Stack
- Node.js with Express, Helmet, CORS, and morgan
- MariaDB/MySQL via `mysql2/promise`
- Auth with bcrypt, JWT, and email verification (Nodemailer)
- Validation with Zod

## Getting started
1. Copy environment settings:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the dev server:
   ```bash
   npm run dev
   ```

## API overview (MVP)
- `GET /health` — confirms server and DB connectivity.
- `POST /auth/register` — create an account with `email`, `username`, and `password`; sends verification email.
- `GET /auth/verify?token=...` — marks an account as verified.
- `POST /auth/login` — login with email/password, returns JWT.
- `GET /lobby` — lists recent lobbies.
- `POST /lobby` — create lobby (requires `Authorization: Bearer <token>` header).

## Schema notes
The service auto-creates minimal tables to bootstrap development:
- `abn_users` — user credentials, verification token, timestamps.
- `abn_sessions` — lobby metadata referencing `abn_users`.

These are intended to coexist with the existing AdventureBot schema and can be expanded to mirror the full game data model.

## Development roadmap
- Mirror game session orchestration endpoints so web and Discord clients share saves.
- Add invitation emails and magic-link join flow.
- Build browser UI (landing page, lobby, session view) and connect to these APIs.
- Harden security: rate limiting, better audit trails, production-ready email transport.
