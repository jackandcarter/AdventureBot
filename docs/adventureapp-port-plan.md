# AdventureApp Port Plan

## Purpose
This document inventories AdventureBot systems that must be mirrored in the AdventureApp web experience and highlights Discord-specific behaviors that require web replacements.

## Discord-only surfaces to rework
- **Hub and tutorial surfaces** rely on Discord embeds populated from database rows; the web client will need rich UI equivalents for the main hub, tutorial pagination, and high-score views, using the same content tables (e.g., `hub_embeds`).【F:hub/hub_embed.py†L8-L65】
- **Session creation and lobby queueing** currently use private Discord threads plus button-based embeds for start confirmation, so the web lobby must handle room creation, invite/visibility rules, and ready states instead of relying on thread creation and embed buttons.【F:game/session_manager.py†L125-L190】【F:game/game_master.py†L35-L99】
- **In-session controls** are delivered as Discord UI components (movement/action buttons) that are enabled/disabled per turn; the web UI should render equivalent controls with stateful enabling and integrate vendor/shop affordances when present.【F:game/session_manager.py†L17-L75】

## Core systems to preserve

### Session lifecycle and state container
- Game sessions are tracked in-memory with `GameSession`, which holds player order, current turn, dungeon state, battle snapshots, trance state, cooldown timers, status effects, and rolling logs to cap size; the web backend needs an equivalent session store with persistence/locking to avoid double-turns.【F:core/game_session.py†L11-L200】
- Session creation seeds both database rows and the in-memory `GameSession`, adding the creator as the first player and mapping sessions to Discord thread IDs; the web service should replace thread IDs with lobby/session identifiers but preserve the same initialization steps and limits (six players, ownership, turn seed).【F:game/session_manager.py†L125-L190】

### Lobby flow and queueing
- The bot builds a queue embed listing up to six player slots and exposes a "Start Game" button; AdventureApp should render a lobby card with join slots, owner controls, and server-side validation that mirrors the same max-player constraint and start gating.【F:game/game_master.py†L35-L99】
- Hub interactions fetch tutorial/high-score embeds from the database; the web lobby should reuse those queries through API endpoints to show the same information with client-side pagination/sorting.【F:hub/hub_embed.py†L8-L117】

### Dungeon generation and room behaviors
- Procedural dungeons span multiple floors with carved mazes, random loops, staircase placement, miniboss/boss/shop/locked rooms, and vendor instancing, all configured by difficulty rules and template fetches from MySQL; the web backend should port this generator and keep template-lookup semantics to maintain odds and room mixes.【F:game/dungeon_generator.py†L17-L119】

### Combat, abilities, and status logic
- Battles are managed by `BattleSystem`, which wires the `AbilityEngine`, renders HP/cooldown bars, applies status modifiers to stats, grants one-time speed advantages from haste/slow, and resolves elemental crystal challenges; the web engine must replicate these calculations and state transitions to keep turn order and buffs identical.【F:game/battle_system.py†L1-L150】
- The `AbilityEngine` drives elemental resistance lookups, JRPG ratio-based damage with variance, and status-effect enrichment/attachment using database tables (`enemy_resistances`, `status_effects`, `ability_status_effects`), so ported combat should keep these database-driven formulas and schema expectations.【F:utils/ability_engine.py†L31-L200】
- Auto-revive and inventory-driven survivability hinge on scanning item effects in player inventories; ensure the web service preserves these checks so revival triggers and key usage match the bot.【F:game/game_master.py†L134-L159】

### Items, keys, and progression rules
- Key/quest items gate locked doors and interactions, with helper checks in session utilities; the web app should mirror this by persisting key counts per player and consuming them on unlock actions.【F:game/session_manager.py†L99-L124】
- The minimap/local-map rendering uses room-type emojis and discovery/reveal logic; AdventureApp should expose the same five-by-five view around the player and consistent iconography, swapping emojis for sprites if desired but keeping visibility rules.【F:game/game_master.py†L160-L190】

### Persistence and logging
- Session and battle logs are truncated to the most recent entries before being written back to the database, keeping on-channel displays concise; web endpoints should stream and paginate logs while respecting the same retention limits to avoid bloat.【F:game/game_master.py†L192-L220】
- All gameplay relies on MySQL-backed tables for rules (difficulties, templates, resistances, items, status effects), so the MariaDB schema must be migrated intact or compatibility shims added to preserve existing data expectations.【F:game/dungeon_generator.py†L71-L119】【F:utils/ability_engine.py†L31-L200】

## Web adaptation recommendations
- Replace Discord embeds/views with a SPA UI (e.g., React with animation libraries like Framer Motion or GSAP) and a WebSocket channel for lobby/session updates so button states and logs update live.
- Mirror in-memory session handling with a server-side cache (Redis or in-process with optimistic locking) backed by MariaDB persistence; include reconnection and idle-timeout rules similar to thread cleanup.
- Preserve turn-based flow by exposing APIs for action submission and turn resolution; surface cooldown bars, trance meters, status chips, and elemental hints in the UI using the same underlying calculations.
- Add lobby discovery/filters and invite codes to supersede Discord thread discovery while retaining the six-player cap and start gating from the existing queue logic.
