import { NextFunction, Request, Response, Router } from 'express';
import { z } from 'zod';
import { HttpError } from '../errors/http-error.js';
import { lobbyStore } from '../services/lobby-store.js';
import { sessionStore } from '../services/session-store.js';
import { Difficulty } from '../services/types.js';
import { serializeSession } from '../services/session-serializer.js';
import { difficultyKeys } from '../services/difficulties.js';

export const sessionsRouter = Router();

const createSessionSchema = z.object({
  ownerName: z.string().min(1),
  difficulty: z.enum(difficultyKeys).default('easy'),
  allowJoinMidgame: z.boolean().optional().default(true),
  password: z.string().min(4).max(50).optional(),
  maxPlayers: z.number().int().min(1).max(10).optional(),
});

sessionsRouter.post('/sessions', (req, res, next) => {
  try {
    const payload = createSessionSchema.parse(req.body);
    const session = sessionStore.createSession({
      ownerName: payload.ownerName,
      difficulty: payload.difficulty as Difficulty,
      allowJoinMidgame: payload.allowJoinMidgame,
      password: payload.password,
      maxPlayers: payload.maxPlayers,
    });
    lobbyStore.postSystemMessage(
      `${payload.ownerName} created a ${payload.difficulty} lobby (${session.players.length}/${session.maxPlayers}).`,
      session.id,
    );

    res.status(201).json({
      sessionId: session.id,
      ownerPlayerId: session.players[0].id,
      state: serializeSession(session),
    });
  } catch (error) {
    next(error);
  }
});

const joinSessionSchema = z.object({
  playerName: z.string().min(1),
  password: z.string().min(1).max(50).optional(),
});

const startSessionSchema = z.object({
  playerId: z.string().uuid(),
});

sessionsRouter.post('/sessions/:sessionId/join', (req, res, next) => {
  try {
    const body = joinSessionSchema.parse(req.body);
    const session = sessionStore.joinSession(req.params.sessionId, body.playerName, body.password);
    const newPlayer = session.players[session.players.length - 1];

    lobbyStore.postSystemMessage(
      `${body.playerName} joined the lobby (${session.players.length}/${session.maxPlayers}).`,
      session.id,
    );

    res.status(201).json({ playerId: newPlayer.id, state: serializeSession(session) });
  } catch (error) {
    next(error);
  }
});

sessionsRouter.post('/sessions/:sessionId/start', (req, res, next) => {
  try {
    const body = startSessionSchema.parse(req.body);
    const session = sessionStore.startSession(req.params.sessionId, body.playerId);

    lobbyStore.postSystemMessage(
      `${session.ownerName} started a ${session.difficulty} run (${session.players.length}/${session.maxPlayers}).`,
      session.id,
    );

    res.json({ state: serializeSession(session) });
  } catch (error) {
    next(error);
  }
});

sessionsRouter.get('/sessions/:sessionId', (req, res, next) => {
  try {
    const session = sessionStore.getSession(req.params.sessionId);
    res.json({ state: serializeSession(session) });
  } catch (error) {
    next(error);
  }
});

const moveSchema = z.object({
  playerId: z.string().uuid(),
  direction: z.enum(['north', 'south', 'east', 'west']),
});

sessionsRouter.post('/sessions/:sessionId/actions/move', (req, res, next) => {
  try {
    const body = moveSchema.parse(req.body);
    const result = sessionStore.movePlayer(req.params.sessionId, body.playerId, body.direction);

    res.json({
      events: result.events,
      room: result.room,
      state: serializeSession(result.session),
    });
  } catch (error) {
    next(error);
  }
});

sessionsRouter.use((err: unknown, _req: Request, res: Response, next: NextFunction) => {
  if (err instanceof HttpError) {
    res.status(err.statusCode).json({ message: err.message });
    return;
  }

  next(err);
});
