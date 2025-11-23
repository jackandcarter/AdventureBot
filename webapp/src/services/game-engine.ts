import crypto from 'crypto';
import { HttpError } from '../errors/http-error.js';
import { createSeededRng, pickFrom, randomInt } from './random.js';
import { baseRoomTypes, floorRoomRules } from './floor-room-rules.js';
import { difficultyDefinitions, getDifficultyDefinition } from './difficulties.js';
import {
  CreateSessionOptions,
  Difficulty,
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

const enemyTemplates: Record<Difficulty, Stats> = {
  easy: { maxHealth: 24, health: 24, attack: 6, defense: 2 },
  medium: { maxHealth: 30, health: 30, attack: 8, defense: 3 },
  hard: { maxHealth: 40, health: 40, attack: 10, defense: 4 },
  crazy_catto: { maxHealth: 52, health: 52, attack: 12, defense: 6 },
};

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const describeRoom = (room: RoomState) => {
  switch (room.kind) {
    case 'monster':
      return 'a hostile creature blocks the path';
    case 'item':
      return 'a gleaming treasure chest awaits';
    case 'locked':
      return 'a locked door stands in your way';
    case 'staircase_down':
      return 'a staircase descends to the next floor';
    case 'staircase_up':
      return 'a staircase rises back to safety';
    case 'boss':
      return 'a powerful foe defends this chamber';
    case 'shop':
      return 'a wandering merchant offers wares';
    case 'trap':
      return 'the floor bristles with hidden traps';
    case 'illusion':
      return 'shifting illusions distort the hallway';
    case 'exit':
      return 'a path back to the entrance glows faintly';
    case 'safe':
      return 'quiet stone corridors stretch forward';
    case 'entrance':
      return 'the party gathers here';
    default:
      return 'quiet stone corridors stretch forward';
  }
};

const createEmptyFloor = (
  width: number,
  height: number,
  floorIndex: number,
  seed: string,
  isBasement = false,
): FloorState => {
  const rng = createSeededRng(`${seed}:floor:${floorIndex}`);
  const rooms: RoomState[][] = [];
  for (let y = 0; y < height; y += 1) {
    const row: RoomState[] = [];
    for (let x = 0; x < width; x += 1) {
      row.push({
        position: { x, y },
        kind: 'safe',
        discovered: false,
        cleared: true,
        locked: false,
        seed: `${seed}:${floorIndex}:${x},${y}`,
      });
    }
    rooms.push(row);
  }

  const start: Position = { x: Math.floor(width / 2), y: Math.floor(height / 2) };
  const stairs: Position = { x: randomInt(rng, 0, width - 1), y: randomInt(rng, 0, height - 1) };
  rooms[start.y][start.x].kind = 'entrance';
  rooms[start.y][start.x].cleared = true;
  rooms[start.y][start.x].discovered = true;
  rooms[stairs.y][stairs.x].kind = 'staircase_down';
  rooms[stairs.y][stairs.x].cleared = false;
  rooms[stairs.y][stairs.x].legend = 'Advance to the next floor';

  return { index: floorIndex, width, height, start, stairs, rooms, isBasement };
};

const pickFloorRules = (difficulty: Difficulty, floorIndex: number) => {
  const floorNumber = floorIndex + 1;
  return floorRoomRules.filter(
    (rule) => rule.difficulty === difficulty && (rule.floorNumber === null || rule.floorNumber === floorNumber),
  );
};

const sprinkleRooms = (floor: FloorState, difficulty: Difficulty) => {
  const rng = createSeededRng(`${floor.start.x},${floor.start.y}:${difficulty}:${floor.index}`);
  const definition = difficultyDefinitions[difficulty];
  const rules = pickFloorRules(difficulty, floor.index);
  const occupied = new Set<string>([`${floor.start.x},${floor.start.y}`, `${floor.stairs.x},${floor.stairs.y}`]);
  const occupy = (pos: Position) => occupied.add(`${pos.x},${pos.y}`);
  occupy(floor.stairs);
  occupy(floor.start);

  const availableCells = floor.width * floor.height - occupied.size;
  const baseDensity = Math.min(definition.minRooms, availableCells);

  const pickCoords = (): Position => {
    return { x: randomInt(rng, 0, floor.width - 1), y: randomInt(rng, 0, floor.height - 1) };
  };

  const applyRule = (roomType: RoomKind, count: number) => {
    for (let i = 0; i < count; i += 1) {
      let pos = pickCoords();
      let attempts = 0;
      while (occupied.has(`${pos.x},${pos.y}`) && attempts < 10) {
        pos = pickCoords();
        attempts += 1;
      }
      if (occupied.has(`${pos.x},${pos.y}`)) continue;
      occupy(pos);
      const room = floor.rooms[pos.y][pos.x];
      room.kind = roomType;
      room.discovered = false;
      room.cleared = roomType === 'safe' || roomType === 'shop' || roomType === 'illusion';
      if (roomType === 'monster' || roomType === 'boss') {
        room.enemy = { ...enemyTemplates[difficulty] };
      }
      if (roomType === 'item') {
        room.loot = [
          {
            id: crypto.randomUUID(),
            name: pickFrom(rng, ['Potion', 'Old Coin', 'Strange Relic', 'Sturdy Key']),
            type: 'treasure',
            quantity: 1,
          },
        ];
      }
      if (roomType === 'locked') {
        room.locked = true;
        room.cleared = false;
      }
      if (roomType === 'trap') {
        room.legend = 'Watch your step — traps ahead';
      }
      if (roomType === 'illusion') {
        room.legend = 'Illusory walls hide secrets';
      }
    }
  };

  const estimatedCells = baseDensity || availableCells;
  rules.forEach((rule) => {
    const desired = Math.min(rule.maxPerFloor, Math.max(1, Math.round(rule.chance * estimatedCells)));
    applyRule(rule.roomType, desired);
  });

  if (!rules.length) {
    baseRoomTypes.forEach((type) => {
      const weight = type === 'monster' ? definition.enemyChance : 0.08;
      applyRule(type, Math.max(1, Math.floor(weight * estimatedCells)));
    });
  }

  const hasLock = floor.rooms.some((row) => row.some((r) => r.locked));
  const hasKey = floor.rooms.some((row) => row.some((r) => r.loot?.some((l) => l.name === 'Sturdy Key')));
  if (hasLock && !hasKey) {
    applyRule('item', 1);
  }

  const isFinalFloor = !floor.isBasement && floor.index === Math.max(0, definition.maxFloors - 1);
  if (isFinalFloor) {
    const room = floor.rooms[floor.stairs.y][floor.stairs.x];
    room.kind = 'boss';
    room.cleared = false;
    room.enemy = { maxHealth: 80, health: 80, attack: 16, defense: 7 };
    room.legend = 'The final encounter awaits';
  }
};

const createDungeon = (difficulty: Difficulty, seed: string): DungeonState => {
  const definition = getDifficultyDefinition(difficulty);
  const floors: FloorState[] = [];
  const rng = createSeededRng(`${seed}:floors`);
  const totalFloors = randomInt(rng, definition.minFloors, definition.maxFloors);
  const includeBasement = rng() < definition.basementChance;
  const basementFloors = includeBasement ? 1 : 0;
  const total = totalFloors + basementFloors;

  for (let i = 0; i < total; i += 1) {
    const isBasement = includeBasement && i === total - 1 && basementFloors > 0;
    const floor = createEmptyFloor(definition.width, definition.height, i, seed, isBasement);
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
    const definition = getDifficultyDefinition(options.difficulty);
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
      difficultySettings: definition,
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
    if (next.x < 0 || next.y < 0 || next.x >= floor.width || next.y >= floor.height) {
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
      events.push(`${player.name} unlocks the door.`);
    }

    if (room.kind === 'monster' || room.kind === 'boss') {
      events.push(resolveCombat(room, player));
    }

    const lootLog = collectLoot(room, player);
    if (lootLog) events.push(lootLog);

    if ((room.kind === 'staircase_down' || room.kind === 'staircase_up') && room.cleared) {
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

    if (room.kind === 'trap') {
      const trapDamage = clamp(randomInt(createSeededRng(room.seed), 5, 12), 1, player.stats.health);
      player.stats.health = clamp(player.stats.health - trapDamage, 0, player.stats.maxHealth);
      events.push(`${player.name} is hurt by a trap for ${trapDamage} damage.`);
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
