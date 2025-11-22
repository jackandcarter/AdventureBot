import express from 'express';
import pinoHttp from 'pino-http';
import { logger } from './logger.js';
import { healthRouter } from './routes/health.js';
import { lobbyRouter } from './routes/lobby.js';
import { sessionsRouter } from './routes/sessions.js';
import { HttpError } from './errors/http-error.js';

export const createApp = () => {
  const app = express();

  app.use(pinoHttp({ logger }));
  app.use(express.json());

  app.use(healthRouter);
  app.use('/api', lobbyRouter);
  app.use('/api', sessionsRouter);

  app.use((req, res) => {
    res.status(404).json({ message: `Route not found: ${req.method} ${req.path}` });
  });

  app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    if (err instanceof HttpError) {
      res.status(err.statusCode).json({ message: err.message });
      return;
    }

    logger.error({ err }, 'Unhandled error');
    res.status(500).json({ message: 'Internal server error' });
  });

  return app;
};
