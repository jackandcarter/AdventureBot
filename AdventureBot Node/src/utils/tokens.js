import crypto from 'crypto';

export const generateVerificationToken = () => crypto.randomBytes(24).toString('hex');
