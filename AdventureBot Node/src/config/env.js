import dotenv from 'dotenv';

dotenv.config();

const number = (value, fallback) => {
  const parsed = Number(value);
  return Number.isNaN(parsed) ? fallback : parsed;
};

export const config = {
  env: process.env.NODE_ENV || 'development',
  port: number(process.env.PORT, 8080),
  publicAppUrl: process.env.PUBLIC_APP_URL || 'http://localhost:5173',
  emailVerificationUrl: process.env.EMAIL_VERIFICATION_URL || 'http://localhost:8080/auth/verify',
  jwt: {
    secret: process.env.JWT_SECRET || 'dev-secret',
    expiresIn: process.env.JWT_EXPIRES_IN || '1d'
  },
  bcryptRounds: number(process.env.BCRYPT_ROUNDS, 10),
  db: {
    host: process.env.DB_HOST || 'localhost',
    port: number(process.env.DB_PORT, 3306),
    user: process.env.DB_USER || 'adventurebot',
    password: process.env.DB_PASSWORD || 'changeme',
    database: process.env.DB_NAME || 'adventurebot',
    connectionLimit: number(process.env.DB_CONNECTION_LIMIT, 10)
  },
  email: {
    from: process.env.EMAIL_FROM || 'AdventureBot <no-reply@example.com>',
    smtpHost: process.env.SMTP_HOST || 'localhost',
    smtpPort: number(process.env.SMTP_PORT, 25),
    smtpUser: process.env.SMTP_USER,
    smtpPass: process.env.SMTP_PASS
  }
};
