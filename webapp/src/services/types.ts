export type Difficulty = 'easy' | 'normal' | 'hard';

export type SessionStatus = 'waiting' | 'in_progress';

export interface Position {
  x: number;
  y: number;
}

export type RoomType = 'entrance' | 'empty' | 'enemy' | 'treasure' | 'stairs';

export interface Player {
  id: string;
  name: string;
  position: Position;
  health: number;
}

export interface GameSession {
  id: string;
  difficulty: Difficulty;
  ownerName: string;
  createdAt: string;
  gridSize: number;
  grid: RoomType[][];
  players: Player[];
  turnIndex: number;
  log: string[];
  status: SessionStatus;
  allowJoinMidgame: boolean;
  password?: string | null;
  maxPlayers: number;
}

export interface MoveResult {
  session: GameSession;
  movedPlayer: Player;
  room: RoomType;
  description: string;
}

export interface CreateSessionOptions {
  ownerName: string;
  difficulty: Difficulty;
  allowJoinMidgame?: boolean;
  password?: string | null;
  maxPlayers?: number;
}

export interface ChatMessage {
  id: string;
  author: string;
  body: string;
  timestamp: string;
  type: 'user' | 'system';
  sessionId?: string;
}

export interface LobbyRoomSummary {
  sessionId: string;
  ownerName: string;
  difficulty: Difficulty;
  status: SessionStatus;
  allowJoinMidgame: boolean;
  playerCount: number;
  maxPlayers: number;
  passwordProtected: boolean;
  createdAt: string;
}

export interface LobbyMessage extends ChatMessage {
  sessionSummary?: LobbyRoomSummary;
}

export interface LobbySnapshot {
  messages: LobbyMessage[];
  rooms: LobbyRoomSummary[];
}
