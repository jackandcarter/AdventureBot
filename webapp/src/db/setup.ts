import fs from 'fs';
import path from 'path';
import mysql, { RowDataPacket } from 'mysql2/promise';
import { getEnv } from '../config/env.js';
import { logger } from '../logger.js';

const env = getEnv();

const loadSetupStatements = (): string[] => {
  const sqlPath = path.resolve(process.cwd(), '..', 'database', 'dump.sql');
  const sql = fs.readFileSync(sqlPath, 'utf8');

  const cleaned = sql
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('--'))
    .join('\n');

  return cleaned
    .split(';')
    .map((statement) => statement.trim())
    .filter((statement) => statement.length > 0);
};

const databaseExists = async (connection: mysql.Connection): Promise<boolean> => {
  const [rows] = await connection.query<RowDataPacket[]>(
    'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = ?',
    [env.mysql.database]
  );

  return rows.length > 0;
};

const hasSchema = async (connection: mysql.Connection): Promise<boolean> => {
  const [rows] = await connection.query<RowDataPacket[]>("SHOW TABLES LIKE 'difficulties'");
  return rows.length > 0;
};

export const ensureDatabaseSetup = async (): Promise<void> => {
  const adminConnection = await mysql.createConnection({
    host: env.mysql.host,
    port: env.mysql.port,
    user: env.mysql.user,
    password: env.mysql.password,
  });

  try {
    const exists = await databaseExists(adminConnection);
    if (!exists) {
      await adminConnection.query(`CREATE DATABASE IF NOT EXISTS \`${env.mysql.database}\``);
      logger.info({ database: env.mysql.database }, 'Created missing database');
    }
  } finally {
    await adminConnection.end();
  }

  const connection = await mysql.createConnection({
    host: env.mysql.host,
    port: env.mysql.port,
    user: env.mysql.user,
    password: env.mysql.password,
    database: env.mysql.database,
    multipleStatements: false,
  });

  try {
    const schemaPresent = await hasSchema(connection);
    if (schemaPresent) {
      logger.info('Database schema already present; skipping setup');
      return;
    }

    const statements = loadSetupStatements();
    for (const statement of statements) {
      await connection.query(statement);
    }

    logger.info('Database schema and seed data installed');
  } catch (error) {
    logger.error({ err: error }, 'Database setup failed');
    throw error;
  } finally {
    await connection.end();
  }
};
