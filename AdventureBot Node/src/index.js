import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { config } from './config/env.js';
import { attachDbHealthcheck } from './db/healthcheck.js';
import { authRouter } from './routes/auth.js';
import { lobbyRouter } from './routes/lobby.js';

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

app.get('/health', async (req, res) => {
  const result = await attachDbHealthcheck();
  res.status(result.ok ? 200 : 500).json(result);
});

app.use('/auth', authRouter);
app.use('/lobby', lobbyRouter);

app.use((req, res) => {
  res.status(404).json({ error: 'Not Found' });
});

app.use((err, req, res, next) => {
  // eslint-disable-next-line no-console
  console.error('Unhandled error', err);
  res.status(500).json({ error: 'Internal Server Error' });
});

app.listen(config.port, () => {
  // eslint-disable-next-line no-console
  console.log(`AdventureBot Node listening on port ${config.port}`);
});
