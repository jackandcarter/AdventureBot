import { createApp } from './app.js';
import { getEnv } from './config/env.js';
import { ensureDatabaseSetup } from './db/setup.js';
import { logger } from './logger.js';

const env = getEnv();
const app = createApp();

const startServer = async () => {
  await ensureDatabaseSetup();
  app.listen(env.port, () => {
    logger.info({ port: env.port, nodeEnv: env.nodeEnv }, 'Web app server listening');
  });
};

startServer().catch((error) => {
  logger.error({ err: error }, 'Failed to start server');
});
