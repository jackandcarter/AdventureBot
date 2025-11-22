import pino from 'pino';
import { getEnv } from './config/env.js';

const env = getEnv();

export const logger = pino({
  name: 'adventurebot-webapp',
  level: env.logLevel,
  transport: env.nodeEnv === 'development' ? { target: 'pino-pretty', options: { colorize: true } } : undefined,
});
