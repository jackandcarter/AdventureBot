import { pool } from '../db/pool.js';
import { ensureAuthSchema } from '../db/setup.js';

export const listLobbies = async () => {
  await ensureAuthSchema();
  const [rows] = await pool.query(
    'SELECT id, name, status, owner_id, created_at, updated_at FROM abn_sessions ORDER BY updated_at DESC LIMIT 50'
  );
  return rows;
};

export const createLobby = async ({ ownerId, name }) => {
  await ensureAuthSchema();
  const [result] = await pool.query(
    'INSERT INTO abn_sessions (owner_id, name, status) VALUES (?, ?, "lobby")',
    [ownerId, name]
  );
  return { id: result.insertId };
};
