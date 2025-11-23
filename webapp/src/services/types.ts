export type Difficulty = 'easy' | 'medium' | 'hard' | 'crazy_catto';

export interface DifficultyDefinition {
  key: Difficulty;
  name: string;
  width: number;
  height: number;
  minFloors: number;
  maxFloors: number;
  minRooms: number;
  enemyChance: number;
  npcCount: number;
  basementChance: number;
  basementMinRooms: number;
  basementMaxRooms: number;
}

export type SessionStatus = 'waiting' | 'in_progress' | 'completed';

export interface Position {
  x: number;
  y: number;
}

export type RoomKind =
  | 'entrance'
  | 'safe'
  | 'monster'
  | 'item'
  | 'shop'
  | 'boss'
  | 'trap'
  | 'illusion'
  | 'staircase_up'
  | 'staircase_down'
  | 'exit'
  | 'locked';

export interface Stats {
  maxHealth: number;
  health: number;
  attack: number;
  defense: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  type: 'treasure' | 'quest' | 'consumable';
  quantity: number;
}

export interface RoomState {
  position: Position;
  kind: RoomKind;
  discovered: boolean;
  cleared: boolean;
  locked: boolean;
  seed: string;
  enemy?: Stats;
  loot?: InventoryItem[];
  legend?: string;
}

export interface FloorState {
  index: number;
  width: number;
  height: number;
  isBasement: boolean;
  start: Position;
  stairs: Position;
  rooms: RoomState[][];
}

export interface DungeonState {
  seed: string;
  currentFloor: number;
  floors: FloorState[];
}

export interface Player {
  id: string;
  name: string;
  position: Position;
  floor: number;
  stats: Stats;
  inventory: InventoryItem[];
}

export interface GameSession {
  id: string;
  difficulty: Difficulty;
  difficultySettings: DifficultyDefinition;
  ownerName: string;
  createdAt: string;
  players: Player[];
  turnOrder: string[];
  turnIndex: number;
  log: string[];
  status: SessionStatus;
  allowJoinMidgame: boolean;
  password?: string | null;
  maxPlayers: number;
  dungeon: DungeonState;
  version: number;
}

export interface MoveOutcome {
  session: GameSession;
  room: RoomState;
  events: string[];
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
