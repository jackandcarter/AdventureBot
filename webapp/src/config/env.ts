import { config } from 'dotenv';
import path from 'path';
import { z } from 'zod';

const envFile = path.resolve(process.cwd(), '.env');
config({ path: envFile });

const EnvSchema = z.object({
  PORT: z.string().optional().transform((val) => (val ? Number(val) : 8080)),
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  LOG_LEVEL: z
    .enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace', 'silent'])
    .default('info'),
  MYSQL_HOST: z.string().min(1),
  MYSQL_PORT: z
    .string()
    .optional()
    .transform((val) => (val ? Number(val) : 3306)),
  MYSQL_USER: z.string().min(1),
  MYSQL_PASSWORD: z.string().min(1),
  MYSQL_DATABASE: z.string().min(1),
  JWT_SECRET: z.string().min(10),
});

const parsed = EnvSchema.safeParse(process.env);

if (!parsed.success) {
  throw new Error(`Invalid environment configuration: ${JSON.stringify(parsed.error.format(), null, 2)}`);
}

const env = {
  port: parsed.data.PORT,
  nodeEnv: parsed.data.NODE_ENV,
  logLevel: parsed.data.LOG_LEVEL,
  mysql: {
    host: parsed.data.MYSQL_HOST,
    port: parsed.data.MYSQL_PORT,
    user: parsed.data.MYSQL_USER,
    password: parsed.data.MYSQL_PASSWORD,
    database: parsed.data.MYSQL_DATABASE,
  },
  jwtSecret: parsed.data.JWT_SECRET,
};

export type Environment = typeof env;

export const getEnv = (): Environment => env;
