import { GameSession } from './types.js';

export const serializeSession = (session: GameSession) => {
  const currentPlayer = session.players[session.turnIndex];
  const currentPlayerId = currentPlayer?.id;

  return {
    id: session.id,
    difficulty: session.difficulty,
    ownerName: session.ownerName,
    createdAt: session.createdAt,
    gridSize: session.gridSize,
    players: session.players.map((player) => ({
      id: player.id,
      name: player.name,
      position: player.position,
      health: player.health,
    })),
    log: session.log,
    status: session.status,
    allowJoinMidgame: session.allowJoinMidgame,
    passwordProtected: Boolean(session.password),
    maxPlayers: session.maxPlayers,
    turn: currentPlayerId
      ? {
          currentPlayerId,
          currentPlayerName: currentPlayer.name,
        }
      : null,
  };
};
