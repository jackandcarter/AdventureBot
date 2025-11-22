import { Router } from 'express';
import { pingDatabase } from '../db/pool.js';

export const healthRouter = Router();

healthRouter.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

healthRouter.get('/ready', async (_req, res, next) => {
  try {
    await pingDatabase();
    res.json({ status: 'ready' });
  } catch (error) {
    next(error);
  }
});
