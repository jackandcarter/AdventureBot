export type Difficulty = 'easy' | 'normal' | 'hard';

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
}

export interface MoveResult {
  session: GameSession;
  movedPlayer: Player;
  room: RoomType;
  description: string;
}
