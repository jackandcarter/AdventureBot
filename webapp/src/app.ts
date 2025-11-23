import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import cookieParser from 'cookie-parser';
import pinoHttp from 'pino-http';
import { logger } from './logger.js';
import { healthRouter } from './routes/health.js';
import { authRouter } from './routes/auth.js';
import { hubRouter } from './routes/hub.js';
import { lobbyRouter } from './routes/lobby.js';
import { sessionsRouter } from './routes/sessions.js';
import { HttpError } from './errors/http-error.js';
import { requireAuth } from './middleware/auth.js';

export const createApp = () => {
  const app = express();

  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const publicDir = path.join(__dirname, '../public');

  app.use(pinoHttp({ logger }));
  app.use(express.json());
  app.use(cookieParser());
  app.use(express.static(publicDir));

  app.use(healthRouter);
  app.use('/api', authRouter);
  app.use('/api', requireAuth, hubRouter);
  app.use('/api', requireAuth, lobbyRouter);
  app.use('/api', requireAuth, sessionsRouter);

  app.get('/login', (_req, res) => {
    res.sendFile(path.join(publicDir, 'login.html'));
  });

  app.get('/register', (_req, res) => {
    res.sendFile(path.join(publicDir, 'register.html'));
  });

  app.get('/', (_req, res) => {
    res.redirect('/lobby');
  });

  app.get('/lobby', requireAuth, (_req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
  });

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
