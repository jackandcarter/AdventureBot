import crypto from 'crypto';
import jwt from 'jsonwebtoken';
import { ResultSetHeader, RowDataPacket } from 'mysql2/promise';
import { getEnv } from '../config/env.js';
import { pool } from '../db/pool.js';

export type WebUser = {
  id: number;
  email: string;
  displayName: string;
  createdAt: Date;
};

const env = getEnv();

type UserRow = RowDataPacket & {
  id: number;
  email: string;
  display_name: string;
  password_hash: string;
  created_at: string;
};

const mapUserRow = (row: UserRow): WebUser => ({
  id: row.id,
  email: row.email,
  displayName: row.display_name,
  createdAt: new Date(row.created_at),
});

const hashPassword = (password: string, salt?: string): string => {
  const saltValue = salt ?? crypto.randomBytes(16).toString('hex');
  const derivedKey = crypto.pbkdf2Sync(password, saltValue, 100_000, 64, 'sha512').toString('hex');
  return `${saltValue}:${derivedKey}`;
};

const verifyPassword = (password: string, storedHash: string): boolean => {
  const [salt, digest] = storedHash.split(':');
  if (!salt || !digest) return false;
  const hashed = hashPassword(password, salt).split(':')[1];
  const digestBuffer = Buffer.from(digest, 'hex');
  const hashedBuffer = Buffer.from(hashed, 'hex');
  if (digestBuffer.length !== hashedBuffer.length) return false;
  return crypto.timingSafeEqual(digestBuffer, hashedBuffer);
};

export const findUserByEmail = async (email: string): Promise<WebUser | null> => {
  const [rows] = await pool.query<UserRow[]>('SELECT * FROM web_users WHERE email = ?', [email]);
  if (!rows.length) return null;
  return mapUserRow(rows[0]);
};

export const findUserWithPassword = async (email: string): Promise<{ user: WebUser; passwordHash: string } | null> => {
  const [rows] = await pool.query<UserRow[]>('SELECT * FROM web_users WHERE email = ?', [email]);
  if (!rows.length) return null;
  const [row] = rows;
  return { user: mapUserRow(row), passwordHash: row.password_hash };
};

export const findUserById = async (id: number): Promise<WebUser | null> => {
  const [rows] = await pool.query<UserRow[]>('SELECT * FROM web_users WHERE id = ?', [id]);
  if (!rows.length) return null;
  return mapUserRow(rows[0]);
};

export const createUser = async (email: string, displayName: string, password: string): Promise<WebUser> => {
  const passwordHash = hashPassword(password);
  const [result] = await pool.query<ResultSetHeader>(
    'INSERT INTO web_users (email, display_name, password_hash) VALUES (?, ?, ?)',
    [email, displayName, passwordHash]
  );

  const insertedId = result.insertId;
  const createdUser = await findUserById(insertedId);
  if (!createdUser) {
    throw new Error('Failed to load created user');
  }

  return createdUser;
};

export const issueTokenForUser = (user: WebUser): string => {
  return jwt.sign({ sub: user.id, email: user.email }, env.jwtSecret, { expiresIn: '7d' });
};

export const verifyUserPassword = async (email: string, password: string): Promise<WebUser | null> => {
  const record = await findUserWithPassword(email);
  if (!record) return null;
  return verifyPassword(password, record.passwordHash) ? record.user : null;
};
