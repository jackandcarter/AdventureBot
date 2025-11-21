import express from 'express';
import { z } from 'zod';
import jwt from 'jsonwebtoken';
import { config } from '../config/env.js';
import { createLobby, listLobbies } from '../services/lobby.js';

export const lobbyRouter = express.Router();

const createLobbySchema = z.object({
  name: z.string().min(3).max(64)
});

const authenticate = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    return res.status(401).json({ error: 'Missing auth header' });
  }

  const [, token] = authHeader.split(' ');
  try {
    const payload = jwt.verify(token, config.jwt.secret);
    req.user = { id: payload.sub, username: payload.username };
    return next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

lobbyRouter.get('/', async (req, res) => {
  const lobbies = await listLobbies();
  res.json({ lobbies });
});

lobbyRouter.post('/', authenticate, async (req, res) => {
  const parse = createLobbySchema.safeParse(req.body);
  if (!parse.success) {
    return res.status(400).json({ error: 'Invalid payload', details: parse.error.issues });
  }

  const lobby = await createLobby({ ownerId: req.user.id, name: parse.data.name });
  res.status(201).json({ lobby });
});
