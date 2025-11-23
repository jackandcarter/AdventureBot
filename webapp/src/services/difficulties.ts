import { RowDataPacket } from 'mysql2/promise';
import { pool } from '../db/pool.js';
import { logger } from '../logger.js';
import { Difficulty, DifficultyDefinition, difficultyKeys } from './types.js';

export const difficultyOrder: Difficulty[] = [...difficultyKeys];

const defaultDifficultyDefinitions: Record<Difficulty, DifficultyDefinition> = {
  easy: {
    key: 'easy',
    name: 'Easy',
    width: 10,
    height: 10,
    minFloors: 1,
    maxFloors: 1,
    minRooms: 50,
    enemyChance: 0.2,
    npcCount: 2,
    basementChance: 0.1,
    basementMinRooms: 3,
    basementMaxRooms: 5,
  },
  medium: {
    key: 'medium',
    name: 'Medium',
    width: 10,
    height: 10,
    minFloors: 1,
    maxFloors: 2,
    minRooms: 75,
    enemyChance: 0.25,
    npcCount: 3,
    basementChance: 0.15,
    basementMinRooms: 4,
    basementMaxRooms: 6,
  },
  hard: {
    key: 'hard',
    name: 'Hard',
    width: 12,
    height: 12,
    minFloors: 2,
    maxFloors: 3,
    minRooms: 100,
    enemyChance: 0.3,
    npcCount: 3,
    basementChance: 0.2,
    basementMinRooms: 5,
    basementMaxRooms: 8,
  },
  crazy_catto: {
    key: 'crazy_catto',
    name: 'Crazy Catto',
    width: 12,
    height: 12,
    minFloors: 3,
    maxFloors: 4,
    minRooms: 125,
    enemyChance: 0.4,
    npcCount: 3,
    basementChance: 0.25,
    basementMinRooms: 6,
    basementMaxRooms: 10,
  },
};

let difficultyDefinitions: Record<Difficulty, DifficultyDefinition> = { ...defaultDifficultyDefinitions };

type DifficultyRow = RowDataPacket & {
  name: string;
  width: number;
  height: number;
  min_floors: number;
  max_floors: number;
  min_rooms: number;
  enemy_chance: number;
  npc_count: number;
  basement_chance: number;
  basement_min_rooms: number;
  basement_max_rooms: number;
};

const normalizeDifficultyName = (name: string): Difficulty | null => {
  const normalized = name.trim().toLowerCase().replace(/\s+/g, '_');
  return difficultyKeys.includes(normalized as Difficulty) ? (normalized as Difficulty) : null;
};

export const loadDifficultyDefinitionsFromDatabase = async (): Promise<Record<Difficulty, DifficultyDefinition>> => {
  const [rows] = await pool.query<DifficultyRow[]>(
    `SELECT name, width, height, min_floors, max_floors, min_rooms, enemy_chance, npc_count, basement_chance, basement_min_rooms, basement_max_rooms
     FROM difficulties
     ORDER BY difficulty_id ASC`,
  );

  const updated: Record<Difficulty, DifficultyDefinition> = { ...defaultDifficultyDefinitions };

  rows.forEach((row) => {
    const key = normalizeDifficultyName(row.name);
    if (!key) {
      logger.warn({ name: row.name }, 'Skipping unknown difficulty name from database');
      return;
    }

    updated[key] = {
      key,
      name: row.name,
      width: row.width,
      height: row.height,
      minFloors: row.min_floors,
      maxFloors: row.max_floors,
      minRooms: row.min_rooms,
      enemyChance: row.enemy_chance,
      npcCount: row.npc_count,
      basementChance: row.basement_chance,
      basementMinRooms: row.basement_min_rooms,
      basementMaxRooms: row.basement_max_rooms,
    };
  });

  difficultyDefinitions = updated;
  logger.info({ count: Object.keys(updated).length }, 'Loaded difficulty definitions from database');

  return difficultyDefinitions;
};

export const getDifficultyDefinitions = (): Record<Difficulty, DifficultyDefinition> => difficultyDefinitions;

export const getDifficultyDefinition = (key: Difficulty): DifficultyDefinition => difficultyDefinitions[key];

export { difficultyKeys };
