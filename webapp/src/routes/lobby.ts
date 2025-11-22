import { Router } from 'express';
import { z } from 'zod';
import { lobbyStore } from '../services/lobby-store.js';
import { Difficulty } from '../services/types.js';
import { serializeSession } from '../services/session-serializer.js';

export const lobbyRouter = Router();

const messageSchema = z.object({
  author: z.string().min(1),
  body: z.string().min(1),
  sessionId: z.string().uuid().optional(),
});

lobbyRouter.get('/lobby', (_req, res) => {
  const snapshot = lobbyStore.getSnapshot();
  res.json(snapshot);
});

lobbyRouter.post('/lobby/messages', (req, res, next) => {
  try {
    const payload = messageSchema.parse(req.body);
    const message = lobbyStore.postUserMessage(payload.author, payload.body, payload.sessionId);
    res.status(201).json({ message });
  } catch (error) {
    next(error);
  }
});

const createRoomSchema = z.object({
  ownerName: z.string().min(1),
  difficulty: z.enum(['easy', 'normal', 'hard']).default('normal') as unknown as Difficulty,
  allowJoinMidgame: z.boolean().optional().default(true),
  password: z.string().min(4).max(50).optional(),
  maxPlayers: z.number().int().min(1).max(10).optional(),
});

lobbyRouter.post('/lobby/rooms', (req, res, next) => {
  try {
    const payload = createRoomSchema.parse(req.body);
    const session = lobbyStore.createRoom({
      ownerName: payload.ownerName,
      difficulty: payload.difficulty,
      allowJoinMidgame: payload.allowJoinMidgame,
      password: payload.password,
      maxPlayers: payload.maxPlayers,
    });

    res.status(201).json({
      sessionId: session.id,
      ownerPlayerId: session.players[0].id,
      state: serializeSession(session),
      lobby: lobbyStore.getSnapshot(),
    });
  } catch (error) {
    next(error);
  }
});
