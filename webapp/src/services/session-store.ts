import crypto from 'crypto';
import { HttpError } from '../errors/http-error.js';
import { Difficulty, GameSession, MoveResult, Player, RoomType } from './types.js';

const MAX_LOG_ENTRIES = 50;
const MAX_PLAYERS = 6;
const DEFAULT_HEALTH = 100;
const GRID_SIZE = 5;

const ROOM_TYPES: RoomType[] = ['empty', 'enemy', 'treasure', 'stairs'];

const createRoomGrid = (size: number): RoomType[][] => {
  const grid: RoomType[][] = [];

  for (let y = 0; y < size; y += 1) {
    const row: RoomType[] = [];
    for (let x = 0; x < size; x += 1) {
      row.push(ROOM_TYPES[Math.floor(Math.random() * ROOM_TYPES.length)]);
    }
    grid.push(row);
  }

  const center = Math.floor(size / 2);
  grid[center][center] = 'entrance';

  return grid;
};

const describeRoom = (room: RoomType) => {
  switch (room) {
    case 'enemy':
      return 'a lurking enemy presence';
    case 'treasure':
      return 'a glittering treasure cache';
    case 'stairs':
      return 'a staircase leading deeper into the dungeon';
    case 'entrance':
      return 'the entrance to the dungeon';
    default:
      return 'a quiet hallway';
  }
};

class SessionStore {
  private sessions: Map<string, GameSession> = new Map();

  createSession(ownerName: string, difficulty: Difficulty): GameSession {
    const sessionId = crypto.randomUUID();
    const playerId = crypto.randomUUID();
    const createdAt = new Date().toISOString();
    const grid = createRoomGrid(GRID_SIZE);
    const center = Math.floor(GRID_SIZE / 2);

    const owner: Player = {
      id: playerId,
      name: ownerName,
      position: { x: center, y: center },
      health: DEFAULT_HEALTH,
    };

    const session: GameSession = {
      id: sessionId,
      difficulty,
      ownerName,
      createdAt,
      gridSize: GRID_SIZE,
      grid,
      players: [owner],
      turnIndex: 0,
      log: [`${ownerName} descends into the dungeon.`],
    };

    this.sessions.set(sessionId, session);

    return session;
  }

  joinSession(sessionId: string, playerName: string): GameSession {
    const session = this.sessions.get(sessionId);

    if (!session) {
      throw new HttpError(404, 'Session not found');
    }

    if (session.players.length >= MAX_PLAYERS) {
      throw new HttpError(400, 'This session already has the maximum number of players');
    }

    const center = Math.floor(session.gridSize / 2);
    const player: Player = {
      id: crypto.randomUUID(),
      name: playerName,
      position: { x: center, y: center },
      health: DEFAULT_HEALTH,
    };

    session.players.push(player);
    session.log.push(`${playerName} joins the run.`);
    this.trimLog(session);

    return session;
  }

  getSession(sessionId: string): GameSession {
    const session = this.sessions.get(sessionId);

    if (!session) {
      throw new HttpError(404, 'Session not found');
    }

    return session;
  }

  movePlayer(sessionId: string, playerId: string, direction: 'north' | 'south' | 'east' | 'west'): MoveResult {
    const session = this.getSession(sessionId);
    const playerIndex = session.players.findIndex((player) => player.id === playerId);

    if (playerIndex === -1) {
      throw new HttpError(404, 'Player not part of this session');
    }

    if (session.players[session.turnIndex]?.id !== playerId) {
      throw new HttpError(409, "It's not your turn to move yet");
    }

    const delta = this.directionToDelta(direction);
    const nextPosition = {
      x: session.players[playerIndex].position.x + delta.x,
      y: session.players[playerIndex].position.y + delta.y,
    };

    if (this.isOutOfBounds(nextPosition, session.gridSize)) {
      throw new HttpError(400, 'Cannot move beyond the dungeon walls');
    }

    session.players[playerIndex].position = nextPosition;

    const room = session.grid[nextPosition.y][nextPosition.x];
    const description = `${session.players[playerIndex].name} moved ${direction} and found ${describeRoom(room)}.`;
    session.log.push(description);
    this.trimLog(session);

    session.turnIndex = (session.turnIndex + 1) % session.players.length;

    return { session, movedPlayer: session.players[playerIndex], room, description };
  }

  private directionToDelta(direction: 'north' | 'south' | 'east' | 'west') {
    switch (direction) {
      case 'north':
        return { x: 0, y: -1 };
      case 'south':
        return { x: 0, y: 1 };
      case 'east':
        return { x: 1, y: 0 };
      case 'west':
        return { x: -1, y: 0 };
      default:
        throw new HttpError(400, 'Unknown direction');
    }
  }

  private isOutOfBounds(position: { x: number; y: number }, gridSize: number) {
    return position.x < 0 || position.y < 0 || position.x >= gridSize || position.y >= gridSize;
  }

  private trimLog(session: GameSession) {
    if (session.log.length > MAX_LOG_ENTRIES) {
      session.log.splice(0, session.log.length - MAX_LOG_ENTRIES);
    }
  }
}

export const sessionStore = new SessionStore();
