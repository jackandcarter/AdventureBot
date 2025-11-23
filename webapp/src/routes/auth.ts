import { Response, Router } from 'express';
import { z } from 'zod';
import { getEnv } from '../config/env.js';
import { HttpError } from '../errors/http-error.js';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth.js';
import { createUser, findUserByEmail, issueTokenForUser, verifyUserPassword } from '../services/auth.js';

export const authRouter = Router();

const env = getEnv();
const cookieOptions = {
  httpOnly: true,
  sameSite: 'lax' as const,
  secure: env.nodeEnv === 'production',
  maxAge: 7 * 24 * 60 * 60 * 1000,
  path: '/',
};

const setSessionCookie = (res: Response, token: string) => {
  res.cookie('auth_token', token, cookieOptions);
};

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  displayName: z.string().min(2),
});

authRouter.post('/auth/register', async (req, res, next) => {
  try {
    const { email, password, displayName } = registerSchema.parse(req.body);
    const normalizedEmail = email.toLowerCase();
    const existing = await findUserByEmail(normalizedEmail);

    if (existing) {
      throw new HttpError(409, 'An account already exists for that email');
    }

    const user = await createUser(normalizedEmail, displayName, password);
    const token = issueTokenForUser(user);
    setSessionCookie(res, token);

    res.json({ user, token });
  } catch (error) {
    next(error);
  }
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

authRouter.post('/auth/login', async (req, res, next) => {
  try {
    const { email, password } = loginSchema.parse(req.body);
    const normalizedEmail = email.toLowerCase();
    const user = await verifyUserPassword(normalizedEmail, password);

    if (!user) {
      throw new HttpError(401, 'Invalid email or password');
    }

    const token = issueTokenForUser(user);
    setSessionCookie(res, token);

    res.json({ user, token });
  } catch (error) {
    next(error);
  }
});

authRouter.get('/auth/me', requireAuth, (req, res) => {
  const { user } = req as AuthenticatedRequest & { cookies?: Record<string, string> };
  const token = (req as { cookies?: Record<string, string> }).cookies?.auth_token;
  res.json({ user, token });
});
