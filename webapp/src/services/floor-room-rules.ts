import { Difficulty, RoomKind } from './types.js';

export interface FloorRoomRule {
  difficulty: Difficulty;
  floorNumber: number | null;
  roomType: RoomKind;
  chance: number;
  maxPerFloor: number;
}

// Seed data mirrors MERGED_FLOOR_ROOM_RULES in database_setup.py
export const floorRoomRules: FloorRoomRule[] = [
  { difficulty: 'easy', floorNumber: 1, roomType: 'safe', chance: 0.5, maxPerFloor: 20 },
  { difficulty: 'easy', floorNumber: 1, roomType: 'monster', chance: 0.3, maxPerFloor: 10 },
  { difficulty: 'easy', floorNumber: 1, roomType: 'item', chance: 0.1, maxPerFloor: 5 },
  { difficulty: 'easy', floorNumber: 1, roomType: 'locked', chance: 0.05, maxPerFloor: 2 },
  { difficulty: 'easy', floorNumber: 1, roomType: 'staircase_down', chance: 0.05, maxPerFloor: 1 },
  { difficulty: 'easy', floorNumber: null, roomType: 'boss', chance: 0, maxPerFloor: 1 },
  { difficulty: 'medium', floorNumber: null, roomType: 'boss', chance: 0, maxPerFloor: 1 },
  { difficulty: 'hard', floorNumber: null, roomType: 'boss', chance: 0, maxPerFloor: 1 },
  { difficulty: 'crazy_catto', floorNumber: null, roomType: 'boss', chance: 0, maxPerFloor: 1 },
];

export const baseRoomTypes: RoomKind[] = [
  'safe',
  'monster',
  'item',
  'shop',
  'trap',
  'illusion',
  'locked',
  'staircase_down',
];
