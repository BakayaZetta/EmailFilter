const userModel = require('../models/userModel');
const authSecurityModel = require('../models/authSecurityModel');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { validationResult } = require('express-validator');
const { verifyCaptchaToken } = require('../services/captchaService');
const { sendVerificationEmail } = require('../services/mailerService');
const {
  createVerificationChallenge,
  consumeVerificationChallenge,
  getRecentVerificationChallenge
} = require('../services/verificationService');

const LOGIN_CAPTCHA_THRESHOLD = Number(process.env.LOGIN_CAPTCHA_THRESHOLD || 3);
const LOCKOUT_THRESHOLD = Number(process.env.LOGIN_LOCKOUT_THRESHOLD || 5);
const LOCKOUT_MINUTES = Number(process.env.LOGIN_LOCKOUT_MINUTES || 15);
const REMEMBER_ME_TRUST_DAYS = Number(process.env.REMEMBER_ME_TRUST_DAYS || 30);
const RESEND_COOLDOWN_SECONDS = Number(process.env.VERIFICATION_RESEND_COOLDOWN_SECONDS || 60);

const resendTracker = new Map();

const getRequestIp = (req) => req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown';

const issueJwt = (user) => jwt.sign(
  { userId: user.ID_Utilisateur, email: user.Email, role: user.Role },
  process.env.JWT_SECRET,
  { expiresIn: '24h' }
);

const formatUserResponse = (user) => ({
  id: user.ID_Utilisateur,
  firstName: user.Prenom,
  lastName: user.Nom,
  email: user.Email,
  role: user.Role
});

const formatAdminUserResponse = (user) => ({
  id: user.ID_Utilisateur,
  firstName: user.Prenom,
  lastName: user.Nom,
  email: user.Email,
  role: user.Role,
  createdAt: user.created_at || null,
  lastLoginAt: user.last_login_at || null,
});

const logAudit = async (req, payload) => {
  await authSecurityModel.logAuthEvent({
    ...payload,
    ipAddress: getRequestIp(req),
    userAgent: req.headers['user-agent'] || null
  });
};

exports.getUsers = async (req, res) => {
  try {
    const users = await userModel.getUsers();
    res.status(200).json(users.map(formatAdminUserResponse));
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.getUserById = async (req, res) => {
  try {
    const users = await userModel.getUserById(req.params.id);
    if (users.length === 0) {
      res.status(404).json({ message: 'User not found' });
    } else {
      res.status(200).json(formatAdminUserResponse(users[0]));
    }
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.requestRegisterVerification = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { firstName, lastName, email, password } = req.body;

  try {
    const normalizedEmail = String(email).toLowerCase().trim();
    const existingUser = await userModel.getUserByEmail(normalizedEmail);
    if (existingUser) {
      return res.status(409).json({ message: 'User already exists with this email' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const challenge = await createVerificationChallenge({
      email: normalizedEmail,
      purpose: 'register',
      payload: {
        firstName,
        lastName,
        email: normalizedEmail,
        hashedPassword
      }
    });

    await sendVerificationEmail({
      to: normalizedEmail,
      code: challenge.code,
      purpose: 'register'
    });

    await logAudit(req, {
      email: normalizedEmail,
      eventType: 'REGISTER_VERIFICATION_SENT',
      detail: 'Registration verification code sent'
    });

    return res.status(200).json({
      message: 'Verification code sent to your email. Use it to complete registration.'
    });
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.verifyAndRegister = async (req, res) => {
  const { email, code } = req.body;

  if (!email || !code) {
    return res.status(400).json({ message: 'Email and verification code are required' });
  }

  try {
    const normalizedEmail = String(email).toLowerCase().trim();

    const challenge = await consumeVerificationChallenge({
      email: normalizedEmail,
      purpose: 'register',
      token: String(code).trim()
    });

    if (!challenge || !challenge.payload) {
      return res.status(400).json({ message: 'Invalid or expired verification code' });
    }

    const existingUser = await userModel.getUserByEmail(normalizedEmail);
    if (existingUser) {
      return res.status(409).json({ message: 'User already exists with this email' });
    }

    const newUser = await userModel.createUserWithRole({
      firstName: challenge.payload.firstName,
      lastName: challenge.payload.lastName,
      email: challenge.payload.email,
      hashedPassword: challenge.payload.hashedPassword,
      role: 'user'
    });

    const persisted = await userModel.getUserByEmail(newUser.email);
    await userModel.updateLastLoginById(persisted.ID_Utilisateur);

    await logAudit(req, {
      userId: persisted.ID_Utilisateur,
      email: normalizedEmail,
      eventType: 'REGISTER_VERIFIED',
      detail: 'Account created after email verification'
    });

    return res.status(201).json({
      user: formatUserResponse(persisted),
      token: issueJwt(persisted)
    });
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.resendVerification = async (req, res) => {
  const { email, purpose } = req.body;
  const normalizedPurpose = String(purpose || '').toLowerCase();

  if (!email || !['register', 'login'].includes(normalizedPurpose)) {
    return res.status(400).json({ message: 'Valid email and purpose are required' });
  }

  try {
    const normalizedEmail = String(email).toLowerCase().trim();
    const cooldownKey = `${normalizedPurpose}:${normalizedEmail}`;
    const now = Date.now();
    const nextAllowedAt = resendTracker.get(cooldownKey) || 0;

    if (now < nextAllowedAt) {
      const waitSeconds = Math.ceil((nextAllowedAt - now) / 1000);
      return res.status(429).json({
        message: `Please wait ${waitSeconds}s before requesting another code.`
      });
    }

    if (normalizedPurpose === 'register') {
      const latest = await getRecentVerificationChallenge({ email: normalizedEmail, purpose: 'register' });
      if (!latest || latest.Consumed_At) {
        return res.status(400).json({ message: 'No pending registration verification found. Start registration again.' });
      }

      const payload = latest.Payload_JSON ? JSON.parse(latest.Payload_JSON) : null;
      if (!payload) {
        return res.status(400).json({ message: 'No pending registration data found.' });
      }

      const challenge = await createVerificationChallenge({
        email: normalizedEmail,
        purpose: 'register',
        payload
      });

      await sendVerificationEmail({
        to: normalizedEmail,
        code: challenge.code,
        purpose: 'register'
      });
    }

    if (normalizedPurpose === 'login') {
      const user = await userModel.getUserByEmail(normalizedEmail);
      if (!user) {
        return res.status(404).json({ message: 'User not found' });
      }

      const challenge = await createVerificationChallenge({
        email: normalizedEmail,
        purpose: 'login',
        payload: { userId: user.ID_Utilisateur }
      });

      await sendVerificationEmail({
        to: normalizedEmail,
        code: challenge.code,
        purpose: 'login'
      });
    }

    resendTracker.set(cooldownKey, now + RESEND_COOLDOWN_SECONDS * 1000);

    await logAudit(req, {
      email: normalizedEmail,
      eventType: 'VERIFICATION_RESENT',
      detail: `Verification resent for ${normalizedPurpose}`
    });

    return res.status(200).json({ message: 'Verification code resent successfully.' });
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.login = async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const { email, password, captchaToken } = req.body;

  try {
    const normalizedEmail = String(email).toLowerCase().trim();
    const user = await userModel.getUserByEmail(normalizedEmail);

    if (!user) {
      await logAudit(req, {
        email: normalizedEmail,
        eventType: 'LOGIN_FAILED',
        detail: 'Unknown email'
      });
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    if (String(user.Role || '').toLowerCase() === 'disabled') {
      await logAudit(req, {
        userId: user.ID_Utilisateur,
        email: normalizedEmail,
        eventType: 'LOGIN_BLOCKED_DISABLED',
        detail: 'Account disabled'
      });
      return res.status(403).json({ message: 'Account deactivated. Contact an administrator.' });
    }

    if (user.lockout_until && new Date(user.lockout_until) > new Date()) {
      await logAudit(req, {
        userId: user.ID_Utilisateur,
        email: normalizedEmail,
        eventType: 'LOGIN_BLOCKED_LOCKOUT',
        detail: `Locked until ${user.lockout_until}`
      });
      return res.status(423).json({ message: 'Account temporarily locked due to failed attempts.' });
    }

    const failedAttempts = Number(user.failed_login_attempts || 0);
    const suspicious = failedAttempts >= LOGIN_CAPTCHA_THRESHOLD;

    if (suspicious) {
      const isCaptchaValid = await verifyCaptchaToken(captchaToken, getRequestIp(req));
      if (!isCaptchaValid) {
        await logAudit(req, {
          userId: user.ID_Utilisateur,
          email: normalizedEmail,
          eventType: 'LOGIN_CAPTCHA_REQUIRED',
          detail: 'Suspicious login requires captcha'
        });
        return res.status(403).json({
          message: 'CAPTCHA verification is required',
          requiresCaptcha: true
        });
      }
    }

    const passwordMatch = await bcrypt.compare(password, user.Mot_de_passe);
    if (!passwordMatch) {
      const securityState = await userModel.incrementFailedLoginAttempt(
        user.ID_Utilisateur,
        LOCKOUT_THRESHOLD,
        LOCKOUT_MINUTES
      );

      await logAudit(req, {
        userId: user.ID_Utilisateur,
        email: normalizedEmail,
        eventType: 'LOGIN_FAILED',
        detail: `Failed attempts: ${securityState?.failed_login_attempts || 'n/a'}`
      });

      return res.status(401).json({
        message: 'Invalid credentials',
        requiresCaptcha: (securityState?.failed_login_attempts || 0) >= LOGIN_CAPTCHA_THRESHOLD
      });
    }

    await userModel.resetFailedLoginAttempts(user.ID_Utilisateur);

    if (user.verification_trust_until && new Date(user.verification_trust_until) > new Date()) {
      await userModel.updateLastLoginById(user.ID_Utilisateur);
      await logAudit(req, {
        userId: user.ID_Utilisateur,
        email: normalizedEmail,
        eventType: 'LOGIN_SUCCESS_TRUSTED',
        detail: 'Trusted session bypassed email verification'
      });

      return res.status(200).json({
        user: formatUserResponse(user),
        token: issueJwt(user)
      });
    }

    const challenge = await createVerificationChallenge({
      email: normalizedEmail,
      purpose: 'login',
      payload: { userId: user.ID_Utilisateur }
    });

    await sendVerificationEmail({
      to: normalizedEmail,
      code: challenge.code,
      purpose: 'login'
    });

    await logAudit(req, {
      userId: user.ID_Utilisateur,
      email: normalizedEmail,
      eventType: 'LOGIN_VERIFICATION_SENT',
      detail: 'Login verification code sent'
    });

    return res.status(202).json({
      requiresEmailVerification: true,
      message: 'Verification code sent to your email.'
    });
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.verifyLogin = async (req, res) => {
  const { email, code, rememberMe } = req.body;

  if (!email || !code) {
    return res.status(400).json({ message: 'Email and verification code are required' });
  }

  try {
    const normalizedEmail = String(email).toLowerCase().trim();
    const challenge = await consumeVerificationChallenge({
      email: normalizedEmail,
      purpose: 'login',
      token: String(code).trim()
    });

    if (!challenge) {
      return res.status(400).json({ message: 'Invalid or expired verification code' });
    }

    const user = await userModel.getUserByEmail(normalizedEmail);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    if (String(user.Role || '').toLowerCase() === 'disabled') {
      return res.status(403).json({ message: 'Account deactivated. Contact an administrator.' });
    }

    await userModel.updateLastLoginById(user.ID_Utilisateur);
    if (Boolean(rememberMe)) {
      await userModel.setVerificationTrust(user.ID_Utilisateur, REMEMBER_ME_TRUST_DAYS);
    }

    await logAudit(req, {
      userId: user.ID_Utilisateur,
      email: normalizedEmail,
      eventType: 'LOGIN_VERIFIED',
      detail: `Login verified. rememberMe=${Boolean(rememberMe)}`
    });

    return res.status(200).json({
      user: formatUserResponse(user),
      token: issueJwt(user)
    });
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};
