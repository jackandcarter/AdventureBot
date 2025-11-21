import express from 'express';
import { z } from 'zod';
import { loginUser, registerUser, verifyEmail } from '../services/auth.js';

export const authRouter = express.Router();

const registerSchema = z.object({
  email: z.string().email(),
  username: z.string().min(3).max(32),
  password: z.string().min(8)
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

authRouter.post('/register', async (req, res) => {
  const parse = registerSchema.safeParse(req.body);
  if (!parse.success) {
    return res.status(400).json({ error: 'Invalid payload', details: parse.error.issues });
  }

  const result = await registerUser(parse.data);
  if (!result.ok) {
    return res.status(result.status || 400).json({ error: result.error });
  }

  return res.status(201).json({
    userId: result.userId,
    message: 'Registration successful, check your email to verify your account'
  });
});

authRouter.post('/login', async (req, res) => {
  const parse = loginSchema.safeParse(req.body);
  if (!parse.success) {
    return res.status(400).json({ error: 'Invalid payload', details: parse.error.issues });
  }

  const result = await loginUser(parse.data);
  if (!result.ok) {
    return res.status(result.status || 400).json({ error: result.error });
  }

  return res.status(200).json({ token: result.token, user: result.user });
});

authRouter.get('/verify', async (req, res) => {
  const token = req.query.token;
  if (!token) {
    return res.status(400).json({ error: 'Missing verification token' });
  }

  const result = await verifyEmail(token);
  if (!result.ok) {
    return res.status(result.status || 400).json({ error: result.error });
  }

  return res.status(200).json({ message: 'Email verified' });
});
