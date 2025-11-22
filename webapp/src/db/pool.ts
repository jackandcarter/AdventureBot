import mysql from 'mysql2/promise';
import { getEnv } from '../config/env.js';
import { logger } from '../logger.js';

const env = getEnv();

export const pool = mysql.createPool({
  host: env.mysql.host,
  port: env.mysql.port,
  user: env.mysql.user,
  password: env.mysql.password,
  database: env.mysql.database,
  waitForConnections: true,
  connectionLimit: 10,
});

export const pingDatabase = async (): Promise<void> => {
  try {
    const connection = await pool.getConnection();
    await connection.ping();
    connection.release();
  } catch (error) {
    logger.error({ err: error }, 'Database ping failed');
    throw error;
  }
};
