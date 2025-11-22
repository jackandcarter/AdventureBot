import { HttpError } from '../errors/http-error.js';
import { GameEngine } from './game-engine.js';
import { CreateSessionOptions, GameSession, LobbyRoomSummary, MoveOutcome } from './types.js';

class SessionStore {
  private sessions: Map<string, GameSession> = new Map();

  createSession(options: CreateSessionOptions): GameSession {
    if ((options.maxPlayers ?? 1) < 1) {
      throw new HttpError(400, 'A session must allow at least one player');
    }

    const session = GameEngine.createSession(options);

    this.sessions.set(session.id, session);

    return session;
  }

  joinSession(sessionId: string, playerName: string, password?: string | null): GameSession {
    const session = this.sessions.get(sessionId);

    if (!session) {
      throw new HttpError(404, 'Session not found');
    }

    if (session.status === 'in_progress' && !session.allowJoinMidgame) {
      throw new HttpError(403, 'This run is not accepting new players after it started');
    }

    if (session.password && session.password !== password) {
      throw new HttpError(401, 'Incorrect password for this room');
    }

    if (session.players.length >= session.maxPlayers) {
      throw new HttpError(400, 'This session already has the maximum number of players');
    }

    GameEngine.joinSession(session, playerName);
    session.log.push(`${playerName} joins the run.`);
    this.trimLog(session);
    session.version += 1;

    return session;
  }

  getSession(sessionId: string): GameSession {
    const session = this.sessions.get(sessionId);

    if (!session) {
      throw new HttpError(404, 'Session not found');
    }

    return session;
  }

  listSessions(): GameSession[] {
    return Array.from(this.sessions.values());
  }

  movePlayer(sessionId: string, playerId: string, direction: 'north' | 'south' | 'east' | 'west'): MoveOutcome {
    const session = this.getSession(sessionId);
    const result = GameEngine.move(session, playerId, direction);
    this.trimLog(session);
    return result;
  }

  private trimLog(session: GameSession) {
    const MAX_LOG_ENTRIES = 50;
    if (session.log.length > MAX_LOG_ENTRIES) {
      session.log.splice(0, session.log.length - MAX_LOG_ENTRIES);
    }
  }

  summarize(session: GameSession): LobbyRoomSummary {
    return {
      sessionId: session.id,
      ownerName: session.ownerName,
      difficulty: session.difficulty,
      status: session.status,
      allowJoinMidgame: session.allowJoinMidgame,
      playerCount: session.players.length,
      maxPlayers: session.maxPlayers,
      passwordProtected: Boolean(session.password),
      createdAt: session.createdAt,
    };
  }
}

export const sessionStore = new SessionStore();
