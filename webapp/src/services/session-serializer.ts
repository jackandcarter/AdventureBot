import { GameSession } from './types.js';

export const serializeSession = (session: GameSession) => {
  const currentPlayer = session.players.find((player) => player.id === session.turnOrder[session.turnIndex]);

  return {
    id: session.id,
    difficulty: session.difficulty,
    difficultySettings: session.difficultySettings,
    ownerName: session.ownerName,
    ownerId: session.ownerId,
    createdAt: session.createdAt,
    players: session.players.map((player) => ({
      id: player.id,
      name: player.name,
      position: player.position,
      floor: player.floor,
      health: player.stats.health,
      maxHealth: player.stats.maxHealth,
      inventory: player.inventory,
    })),
      dungeon: {
        currentFloor: session.dungeon.currentFloor,
        floors: session.dungeon.floors.map((floor) => ({
          index: floor.index,
          width: floor.width,
          height: floor.height,
          isBasement: floor.isBasement,
          start: floor.start,
          stairs: floor.stairs,
          rooms: floor.rooms.map((row) =>
            row.map((room) => ({
              position: room.position,
              kind: room.kind,
              discovered: room.discovered,
              cleared: room.cleared,
              locked: room.locked,
              enemy: room.enemy ? { ...room.enemy } : undefined,
              loot: room.loot,
              legend: room.legend,
            })),
          ),
        })),
      },
    log: session.log,
    status: session.status,
    allowJoinMidgame: session.allowJoinMidgame,
    passwordProtected: Boolean(session.password),
    maxPlayers: session.maxPlayers,
    turn: currentPlayer
      ? {
          currentPlayerId: currentPlayer.id,
          currentPlayerName: currentPlayer.name,
        }
      : null,
    version: session.version,
  };
};
