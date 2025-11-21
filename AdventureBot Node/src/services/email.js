import nodemailer from 'nodemailer';
import { config } from '../config/env.js';

const transporter = nodemailer.createTransport({
  host: config.email.smtpHost,
  port: config.email.smtpPort,
  auth: config.email.smtpUser
    ? {
        user: config.email.smtpUser,
        pass: config.email.smtpPass
      }
    : undefined
});

export const sendVerificationEmail = async ({ to, token }) => {
  const url = `${config.emailVerificationUrl}?token=${encodeURIComponent(token)}`;
  const message = {
    from: config.email.from,
    to,
    subject: 'Verify your AdventureBot Node account',
    text: `Welcome to AdventureBot! Verify your email to start playing: ${url}`,
    html: `<p>Welcome to AdventureBot!</p><p><a href="${url}">Click here to verify your email</a></p>`
  };

  if (config.env === 'development') {
    // eslint-disable-next-line no-console
    console.log('[DEV email]', message);
    return { previewUrl: url };
  }

  await transporter.sendMail(message);
  return { previewUrl: url };
};
