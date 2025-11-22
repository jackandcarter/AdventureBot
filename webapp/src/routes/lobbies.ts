import express from 'express';
import { lobbyStore } from '../features/lobbies/lobbyStore.js';
import { LobbyVisibility } from '../features/lobbies/types.js';

export const lobbyRouter = express.Router();

const parseVisibility = (visibility?: string): LobbyVisibility | undefined => {
  if (!visibility) return undefined;
  if (visibility === 'public' || visibility === 'private' || visibility === 'invite') {
    return visibility;
  }
  return undefined;
};

lobbyRouter.get('/', (_req, res) => {
  const lobbies = lobbyStore.listPublicLobbies();
  res.json({ lobbies });
});

lobbyRouter.post('/', (req, res) => {
  const { ownerId, name, visibility, maxPlayers } = req.body ?? {};

  if (!ownerId || typeof ownerId !== 'string') {
    return res.status(400).json({ message: 'ownerId is required' });
  }

  const parsedVisibility = parseVisibility(visibility);

  const lobby = lobbyStore.createLobby({
    ownerId,
    name: typeof name === 'string' ? name : undefined,
    visibility: parsedVisibility,
    maxPlayers: typeof maxPlayers === 'number' ? maxPlayers : undefined,
  });

  res.status(201).json({ lobby });
});

lobbyRouter.get('/:lobbyId', (req, res) => {
  const lobby = lobbyStore.getLobby(req.params.lobbyId);

  if (!lobby) {
    return res.status(404).json({ message: 'Lobby not found' });
  }

  res.json({ lobby });
});

lobbyRouter.post('/:lobbyId/join', (req, res) => {
  const { playerId, displayName } = req.body ?? {};

  if (!playerId || typeof playerId !== 'string') {
    return res.status(400).json({ message: 'playerId is required' });
  }

  try {
    const lobby = lobbyStore.joinLobby({
      lobbyId: req.params.lobbyId,
      playerId,
      displayName: typeof displayName === 'string' ? displayName : 'Player',
    });

    res.json({ lobby });
  } catch (err) {
    res.status(400).json({ message: (err as Error).message });
  }
});

lobbyRouter.post('/:lobbyId/leave', (req, res) => {
  const { playerId } = req.body ?? {};

  if (!playerId || typeof playerId !== 'string') {
    return res.status(400).json({ message: 'playerId is required' });
  }

  try {
    const lobby = lobbyStore.leaveLobby({ lobbyId: req.params.lobbyId, playerId });
    res.json({ lobby });
  } catch (err) {
    res.status(400).json({ message: (err as Error).message });
  }
});

lobbyRouter.post('/:lobbyId/ready', (req, res) => {
  const { playerId, ready } = req.body ?? {};

  if (!playerId || typeof playerId !== 'string') {
    return res.status(400).json({ message: 'playerId is required' });
  }

  if (typeof ready !== 'boolean') {
    return res.status(400).json({ message: 'ready flag is required' });
  }

  try {
    const lobby = lobbyStore.setReady({ lobbyId: req.params.lobbyId, playerId, ready });
    res.json({ lobby });
  } catch (err) {
    res.status(400).json({ message: (err as Error).message });
  }
});

lobbyRouter.post('/:lobbyId/start', (req, res) => {
  const { playerId } = req.body ?? {};

  if (!playerId || typeof playerId !== 'string') {
    return res.status(400).json({ message: 'playerId is required' });
  }

  try {
    const lobby = lobbyStore.startLobby({ lobbyId: req.params.lobbyId, playerId });
    res.json({ lobby });
  } catch (err) {
    res.status(400).json({ message: (err as Error).message });
  }
});
