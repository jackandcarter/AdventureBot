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

const ensureWebUsersTable = async (connection: mysql.Connection): Promise<void> => {
  const [rows] = await connection.query<RowDataPacket[]>("SHOW TABLES LIKE 'web_users'");
  if (rows.length > 0) return;

  await connection.query(`
      CREATE TABLE IF NOT EXISTS web_users (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        email         VARCHAR(255) NOT NULL UNIQUE,
        display_name  VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
  logger.info('Created missing web_users table');
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
    if (!schemaPresent) {
      const statements = loadSetupStatements();
      for (const statement of statements) {
        await connection.query(statement);
      }

      logger.info('Database schema and seed data installed');
    }

    await ensureWebUsersTable(connection);
    if (schemaPresent) {
      logger.info('Database schema already present; ensured user table');
    }
  } catch (error) {
    logger.error({ err: error }, 'Database setup failed');
    throw error;
  } finally {
    await connection.end();
  }
};
