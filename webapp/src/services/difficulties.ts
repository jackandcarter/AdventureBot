import { Difficulty, DifficultyDefinition } from './types.js';

export const difficultyOrder: Difficulty[] = ['easy', 'medium', 'hard', 'crazy_catto'];

export const difficultyDefinitions: Record<Difficulty, DifficultyDefinition> = {
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

export const getDifficultyDefinition = (key: Difficulty): DifficultyDefinition => difficultyDefinitions[key];

export const difficultyKeys = Object.keys(difficultyDefinitions) as Difficulty[];
