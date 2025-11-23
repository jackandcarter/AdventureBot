import { Router } from 'express';
import { z } from 'zod';
import {
  fetchHighScores,
  fetchMainHubEmbed,
  fetchTutorialPage,
  HubEmbed,
  HighScoreSort,
} from '../services/hub-content.js';

export const hubRouter = Router();

hubRouter.get('/hub/main', async (_req, res, next) => {
  try {
    const embed = await fetchMainHubEmbed();
    const payload: { embed: HubEmbed | null } = { embed };
    res.json(payload);
  } catch (error) {
    next(error);
  }
});

const tutorialQuery = z.object({
  page: z.coerce.number().int().min(1).default(1),
});

hubRouter.get('/hub/tutorial', async (req, res, next) => {
  try {
    const { page } = tutorialQuery.parse(req.query);
    const result = await fetchTutorialPage(page);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

const highScoreQuery = z.object({
  sort: z
    .enum(['score_value', 'enemies_defeated', 'bosses_defeated', 'gil', 'player_level', 'rooms_visited'])
    .default('score_value'),
  limit: z.coerce.number().int().min(1).max(50).optional().default(20),
});

hubRouter.get('/hub/high-scores', async (req, res, next) => {
  try {
    const { sort, limit } = highScoreQuery.parse(req.query);
    const results = await fetchHighScores(sort as HighScoreSort, limit);
    res.json({ sortBy: sort, results });
  } catch (error) {
    next(error);
  }
});

