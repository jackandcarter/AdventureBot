import { createApp } from './app.js';
import { getEnv } from './config/env.js';
import { logger } from './logger.js';

const env = getEnv();
const app = createApp();

app.listen(env.port, () => {
  logger.info({ port: env.port, nodeEnv: env.nodeEnv }, 'Web app server listening');
});
