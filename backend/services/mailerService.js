const nodemailer = require('nodemailer');

let transporter;

const getTransporter = () => {
  if (transporter) {
    return transporter;
  }

  if (!process.env.SMTP_HOST || !process.env.SMTP_USER || !process.env.SMTP_PASS) {
    return null;
  }

  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT || 587),
    secure: String(process.env.SMTP_SECURE || 'false').toLowerCase() === 'true',
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  });

  return transporter;
};

const sendVerificationEmail = async ({ to, code, purpose }) => {
  const sender = process.env.SMTP_FROM || process.env.SMTP_USER || 'no-reply@detectish.local';
  const subject = purpose === 'register'
    ? 'Bakaya Email Security - Registration verification code'
    : 'Bakaya Email Security - Login verification code';

  const text = `Your verification code is: ${code}. It expires in 10 minutes.`;

  const activeTransporter = getTransporter();
  if (!activeTransporter) {
    if (String(process.env.NODE_ENV || '').toLowerCase() === 'production') {
      throw new Error('SMTP is not configured in production environment');
    }
    console.log(`[MAILER:FALLBACK] to=${to} purpose=${purpose} code=redacted`);
    return { delivered: false, fallback: true };
  }

  await activeTransporter.sendMail({
    from: sender,
    to,
    subject,
    text
  });

  return { delivered: true, fallback: false };
};

module.exports = {
  sendVerificationEmail
};
