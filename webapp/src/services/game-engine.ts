import crypto from 'crypto';
import { HttpError } from '../errors/http-error.js';
import { createSeededRng, pickFrom, randomInt } from './random.js';
import {
  CreateSessionOptions,
  DungeonState,
  FloorState,
  GameSession,
  MoveOutcome,
  Player,
  Position,
  RoomKind,
  RoomState,
  Stats,
} from './types.js';

const DEFAULT_STATS: Stats = { maxHealth: 100, health: 100, attack: 10, defense: 4 };
const MAX_LOG_ENTRIES = 50;
const DEFAULT_GRID = 9;
const DEFAULT_FLOORS = 3;

const enemyTemplates: Record<string, Stats> = {
  easy: { maxHealth: 24, health: 24, attack: 6, defense: 2 },
  normal: { maxHealth: 30, health: 30, attack: 8, defense: 3 },
  hard: { maxHealth: 40, health: 40, attack: 10, defense: 4 },
};

const difficultyKeys: Record<string, number> = { easy: 1, normal: 2, hard: 3 };

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const describeRoom = (room: RoomState) => {
  switch (room.kind) {
    case 'enemy':
      return 'a hostile creature blocks the path';
    case 'treasure':
      return 'a gleaming treasure chest awaits';
    case 'locked':
      return 'a locked door stands in your way';
    case 'stairs':
      return 'a staircase descends to the next floor';
    case 'boss':
      return 'a powerful foe defends this chamber';
    case 'shop':
      return 'a wandering merchant offers wares';
    default:
      return 'quiet stone corridors stretch forward';
  }
};

const createEmptyFloor = (size: number, floorIndex: number, seed: string): FloorState => {
  const rng = createSeededRng(`${seed}:floor:${floorIndex}`);
  const rooms: RoomState[][] = [];
  for (let y = 0; y < size; y += 1) {
    const row: RoomState[] = [];
    for (let x = 0; x < size; x += 1) {
      row.push({
        position: { x, y },
        kind: 'hall',
        discovered: false,
        cleared: true,
        locked: false,
        seed: `${seed}:${floorIndex}:${x},${y}`,
      });
    }
    rooms.push(row);
  }

  const start: Position = { x: Math.floor(size / 2), y: Math.floor(size / 2) };
  const stairs: Position = { x: randomInt(rng, 0, size - 1), y: randomInt(rng, 0, size - 1) };
  rooms[start.y][start.x].kind = 'entrance';
  rooms[start.y][start.x].cleared = true;
  rooms[start.y][start.x].discovered = true;
  rooms[stairs.y][stairs.x].kind = 'stairs';
  rooms[stairs.y][stairs.x].cleared = false;

  return { index: floorIndex, size, start, stairs, rooms };
};

const sprinkleRooms = (floor: FloorState, difficulty: string) => {
  const rng = createSeededRng(`${floor.start.x},${floor.start.y}:${difficulty}:${floor.index}`);
  const density = clamp(6 + difficultyKeys[difficulty] * 2, 4, floor.size * 2);

  const pickCoords = (): Position => {
    return { x: randomInt(rng, 0, floor.size - 1), y: randomInt(rng, 0, floor.size - 1) };
  };

  const occupied = new Set<string>([`${floor.start.x},${floor.start.y}`, `${floor.stairs.x},${floor.stairs.y}`]);
  const occupy = (pos: Position) => occupied.add(`${pos.x},${pos.y}`);
  occupy(floor.stairs);
  occupy(floor.start);

  for (let i = 0; i < density; i += 1) {
    const pos = pickCoords();
    const key = `${pos.x},${pos.y}`;
    if (occupied.has(key)) continue;
    occupy(pos);
    const template = pickFrom(rng, ['enemy', 'treasure', 'locked', 'enemy', 'treasure', 'hall'] as RoomKind[]);
    const room = floor.rooms[pos.y][pos.x];
    room.kind = template;
    room.discovered = false;
    room.cleared = template !== 'enemy' && template !== 'locked';
    if (template === 'enemy') {
      room.enemy = { ...enemyTemplates[difficulty] };
    }
    if (template === 'treasure') {
      room.loot = [
        {
          id: crypto.randomUUID(),
          name: pickFrom(rng, ['Potion', 'Old Coin', 'Strange Relic', 'Sturdy Key']),
          type: 'treasure',
          quantity: 1,
        },
      ];
    }
    if (template === 'locked') {
      room.locked = true;
      room.cleared = false;
    }
  }

  // Ensure a key exists if we spawned locks
  const hasLock = floor.rooms.some((row) => row.some((r) => r.locked));
  if (hasLock) {
    const keySpot = pickCoords();
    const room = floor.rooms[keySpot.y][keySpot.x];
    room.kind = 'treasure';
    room.locked = false;
    room.cleared = false;
    room.loot = [
      { id: crypto.randomUUID(), name: 'Iron Key', type: 'quest', quantity: 1 },
      { id: crypto.randomUUID(), name: 'Rations', type: 'consumable', quantity: 1 },
    ];
  }

  // Boss on final floor guarding stairs
  if (floor.index === DEFAULT_FLOORS - 1) {
    const room = floor.rooms[floor.stairs.y][floor.stairs.x];
    room.kind = 'boss';
    room.cleared = false;
    room.enemy = { maxHealth: 60, health: 60, attack: 14, defense: 6 };
  }
};

const createDungeon = (difficulty: string, seed: string): DungeonState => {
  const floors: FloorState[] = [];
  for (let i = 0; i < DEFAULT_FLOORS; i += 1) {
    const floor = createEmptyFloor(DEFAULT_GRID, i, seed);
    sprinkleRooms(floor, difficulty);
    floors.push(floor);
  }
  return { seed, floors, currentFloor: 0 };
};

const calculateDamage = (rng: () => number, attacker: Stats, defender: Stats) => {
  const base = attacker.attack - Math.floor(defender.defense / 2);
  const variance = randomInt(rng, -2, 3);
  return clamp(base + variance, 1, attacker.attack + 4);
};

const resolveCombat = (room: RoomState, player: Player): string => {
  if (!room.enemy) return 'Nothing to fight here.';
  const rng = createSeededRng(`${room.seed}:battle:${player.id}`);
  const log: string[] = [];
  const foe = { ...room.enemy };
  const stats = player.stats;

  while (foe.health > 0 && stats.health > 0) {
    const playerHit = calculateDamage(rng, stats, foe);
    foe.health = clamp(foe.health - playerHit, 0, foe.maxHealth);
    log.push(`${player.name} strikes for ${playerHit} damage.`);
    if (foe.health <= 0) break;

    const enemyHit = calculateDamage(rng, foe, stats);
    stats.health = clamp(stats.health - enemyHit, 0, stats.maxHealth);
    log.push(`The foe hits back for ${enemyHit} damage.`);
  }

  room.enemy = { ...room.enemy, health: foe.health };
  room.cleared = foe.health <= 0;
  if (room.cleared) {
    log.push(foe.health <= 0 ? 'The enemy is defeated.' : 'The path is clear.');
  }
  return log.join(' ');
};

const collectLoot = (room: RoomState, player: Player): string | null => {
  if (!room.loot || room.loot.length === 0) return null;
  const lootNames = room.loot.map((item) => `${item.name} x${item.quantity}`);
  player.inventory.push(...room.loot);
  room.loot = [];
  room.cleared = true;
  return `${player.name} collects ${lootNames.join(', ')}.`;
};

export class GameEngine {
  static createSession(options: CreateSessionOptions): GameSession {
    const sessionId = crypto.randomUUID();
    const createdAt = new Date().toISOString();
    const dungeon = createDungeon(options.difficulty, sessionId);
    const owner: Player = {
      id: crypto.randomUUID(),
      name: options.ownerName,
      position: { ...dungeon.floors[0].start },
      floor: 0,
      stats: { ...DEFAULT_STATS },
      inventory: [],
    };

    return {
      id: sessionId,
      difficulty: options.difficulty,
      ownerName: options.ownerName,
      createdAt,
      players: [owner],
      turnOrder: [owner.id],
      turnIndex: 0,
      log: [`${options.ownerName} descends into the dungeon.`],
      status: 'waiting',
      allowJoinMidgame: options.allowJoinMidgame ?? true,
      password: options.password,
      maxPlayers: options.maxPlayers ?? 6,
      dungeon,
      version: 1,
    };
  }

  static joinSession(session: GameSession, playerName: string): Player {
    const floor = session.dungeon.floors[session.dungeon.currentFloor];
    const player: Player = {
      id: crypto.randomUUID(),
      name: playerName,
      position: { ...floor.start },
      floor: session.dungeon.currentFloor,
      stats: { ...DEFAULT_STATS },
      inventory: [],
    };

    session.players.push(player);
    session.turnOrder.push(player.id);
    return player;
  }

  static move(session: GameSession, playerId: string, direction: 'north' | 'south' | 'east' | 'west'): MoveOutcome {
    const player = session.players.find((p) => p.id === playerId);
    if (!player) throw new HttpError(404, 'Player not part of this session');
    if (session.turnOrder[session.turnIndex] !== playerId) {
      throw new HttpError(409, "It's not your turn to move yet");
    }

    const delta: Record<typeof direction, Position> = {
      north: { x: 0, y: -1 },
      south: { x: 0, y: 1 },
      east: { x: 1, y: 0 },
      west: { x: -1, y: 0 },
    } as const;

    const floor = session.dungeon.floors[player.floor];
    const next: Position = { x: player.position.x + delta[direction].x, y: player.position.y + delta[direction].y };
    if (next.x < 0 || next.y < 0 || next.x >= floor.size || next.y >= floor.size) {
      throw new HttpError(400, 'Cannot move beyond the dungeon walls');
    }

    const room = floor.rooms[next.y][next.x];
    if (room.locked && !player.inventory.some((item) => item.type === 'quest')) {
      throw new HttpError(423, 'The door is locked. You need a key.');
    }

    player.position = next;
    room.discovered = true;
    const events: string[] = [];

    if (room.locked && player.inventory.some((item) => item.type === 'quest')) {
      room.locked = false;
      room.kind = room.kind === 'locked' ? 'hall' : room.kind;
      events.push(`${player.name} unlocks the door.`);
    }

    if (room.kind === 'enemy' || room.kind === 'boss') {
      events.push(resolveCombat(room, player));
    }

    const lootLog = collectLoot(room, player);
    if (lootLog) events.push(lootLog);

    if (room.kind === 'stairs' && room.cleared) {
      if (session.dungeon.currentFloor < session.dungeon.floors.length - 1) {
        session.dungeon.currentFloor += 1;
        const nextFloor = session.dungeon.floors[session.dungeon.currentFloor];
        player.floor = session.dungeon.currentFloor;
        player.position = { ...nextFloor.start };
        events.push(`${player.name} descends to floor ${session.dungeon.currentFloor + 1}.`);
      } else {
        session.status = 'completed';
        events.push(`${player.name} reaches the final chamber. The run is complete!`);
      }
    }

    const description = `${player.name} moved ${direction} and found ${describeRoom(room)}.`;
    events.unshift(description);

    session.log.push(...events.filter(Boolean));
    if (session.log.length > MAX_LOG_ENTRIES) {
      session.log.splice(0, session.log.length - MAX_LOG_ENTRIES);
    }

    if (session.status === 'waiting') {
      session.status = 'in_progress';
    }

    session.turnIndex = (session.turnIndex + 1) % session.turnOrder.length;
    session.version += 1;

    return { session, room, events };
  }
}

