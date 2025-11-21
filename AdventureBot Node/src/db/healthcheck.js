import { pool } from './pool.js';

export const attachDbHealthcheck = async () => {
  try {
    const [rows] = await pool.query('SELECT 1 AS ok');
    return { ok: rows.length === 1, service: 'db' };
  } catch (error) {
    return { ok: false, service: 'db', error: error.message };
  }
};
