import { NextFunction, Request, Response, Router } from 'express';
import { z } from 'zod';
import { HttpError } from '../errors/http-error.js';
import { sessionStore } from '../services/session-store.js';
import { Difficulty } from '../services/types.js';

export const sessionsRouter = Router();

const createSessionSchema = z.object({
  ownerName: z.string().min(1),
  difficulty: z.enum(['easy', 'normal', 'hard']).default('normal'),
});

sessionsRouter.post('/sessions', (req, res, next) => {
  try {
    const payload = createSessionSchema.parse(req.body);
    const session = sessionStore.createSession(payload.ownerName, payload.difficulty as Difficulty);

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
});

sessionsRouter.post('/sessions/:sessionId/join', (req, res, next) => {
  try {
    const body = joinSessionSchema.parse(req.body);
    const session = sessionStore.joinSession(req.params.sessionId, body.playerName);
    const newPlayer = session.players[session.players.length - 1];

    res.status(201).json({ playerId: newPlayer.id, state: serializeSession(session) });
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
      description: result.description,
      roomType: result.room,
      state: serializeSession(result.session),
    });
  } catch (error) {
    next(error);
  }
});

const serializeSession = (session: ReturnType<typeof sessionStore.getSession>) => {
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
    turn: currentPlayerId
      ? {
          currentPlayerId,
          currentPlayerName: currentPlayer.name,
        }
      : null,
  };
};

sessionsRouter.use((err: unknown, _req: Request, res: Response, next: NextFunction) => {
  if (err instanceof HttpError) {
    res.status(err.statusCode).json({ message: err.message });
    return;
  }

  next(err);
});
