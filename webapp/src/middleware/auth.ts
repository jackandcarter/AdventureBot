import { NextFunction, Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import { getEnv } from '../config/env.js';
import { findUserById, WebUser } from '../services/auth.js';

type TokenPayload = {
  sub: number;
};

export type AuthenticatedRequest = Request & { user?: WebUser };

const env = getEnv();

const extractToken = (req: Request): string | null => {
  const cookieToken = (req as Request & { cookies?: Record<string, string | undefined> }).cookies?.auth_token;
  if (cookieToken) return cookieToken;

  const header = req.header('authorization');
  if (header?.startsWith('Bearer ')) {
    return header.replace('Bearer ', '');
  }

  return null;
};

export const requireAuth = async (req: Request, res: Response, next: NextFunction) => {
  const token = extractToken(req);
  if (!token) {
    res.status(401).json({ message: 'Authentication required' });
    return;
  }

  try {
    const decoded = jwt.verify(token, env.jwtSecret);
    const userId =
      typeof decoded === 'object' && decoded && 'sub' in decoded
        ? Number((decoded as { sub?: string | number }).sub)
        : NaN;

    if (!Number.isFinite(userId)) {
      res.status(401).json({ message: 'Invalid token' });
      return;
    }

    const user = await findUserById(userId);

    if (!user) {
      res.status(401).json({ message: 'Invalid token' });
      return;
    }

    (req as AuthenticatedRequest).user = user;
    next();
  } catch (_error) {
    res.status(401).json({ message: 'Invalid or expired token' });
  }
};
