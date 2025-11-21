import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { pool } from '../db/pool.js';
import { ensureAuthSchema } from '../db/setup.js';
import { config } from '../config/env.js';
import { generateVerificationToken } from '../utils/tokens.js';
import { sendVerificationEmail } from './email.js';

const normalizeEmail = (email) => email.trim().toLowerCase();
const normalizeUsername = (username) => username.trim();

export const registerUser = async ({ email, username, password }) => {
  await ensureAuthSchema();
  const normalizedEmail = normalizeEmail(email);
  const normalizedUsername = normalizeUsername(username);
  const [existing] = await pool.query(
    'SELECT id, email, username FROM abn_users WHERE email = ? OR username = ? LIMIT 1',
    [normalizedEmail, normalizedUsername]
  );

  if (existing.length) {
    const conflict = existing[0].email === normalizedEmail ? 'email' : 'username';
    return { ok: false, status: 409, error: `${conflict} already in use` };
  }

  const verificationToken = generateVerificationToken();
  const passwordHash = await bcrypt.hash(password, config.bcryptRounds);

  const [result] = await pool.query(
    'INSERT INTO abn_users (email, username, password_hash, verification_token) VALUES (?, ?, ?, ?)',
    [normalizedEmail, normalizedUsername, passwordHash, verificationToken]
  );

  await sendVerificationEmail({ to: normalizedEmail, token: verificationToken });

  return { ok: true, userId: result.insertId, verificationToken };
};

export const verifyEmail = async (token) => {
  await ensureAuthSchema();
  const [rows] = await pool.query(
    'SELECT id FROM abn_users WHERE verification_token = ? LIMIT 1',
    [token]
  );

  if (!rows.length) {
    return { ok: false, status: 404, error: 'Verification token not found' };
  }

  const userId = rows[0].id;
  await pool.query(
    'UPDATE abn_users SET email_verified = 1, verification_token = NULL WHERE id = ?',
    [userId]
  );

  return { ok: true };
};

export const loginUser = async ({ email, password }) => {
  await ensureAuthSchema();
  const normalizedEmail = normalizeEmail(email);
  const [rows] = await pool.query(
    'SELECT id, username, password_hash, email_verified FROM abn_users WHERE email = ? LIMIT 1',
    [normalizedEmail]
  );

  if (!rows.length) {
    return { ok: false, status: 401, error: 'Invalid credentials' };
  }

  const user = rows[0];
  const matches = await bcrypt.compare(password, user.password_hash);

  if (!matches) {
    return { ok: false, status: 401, error: 'Invalid credentials' };
  }

  if (!user.email_verified) {
    return { ok: false, status: 403, error: 'Email not verified' };
  }

  const token = jwt.sign({ sub: user.id, username: user.username }, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn
  });

  return { ok: true, token, user: { id: user.id, username: user.username } };
};
