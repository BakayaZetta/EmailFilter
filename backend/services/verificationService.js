const crypto = require('crypto');
const authSecurityModel = require('../models/authSecurityModel');

const TOKEN_EXPIRY_MINUTES = Number(process.env.VERIFICATION_TOKEN_EXPIRY_MINUTES || 10);

const generateCode = () => {
  return String(Math.floor(100000 + Math.random() * 900000));
};

const hashToken = (token) => {
  return crypto.createHash('sha256').update(token).digest('hex');
};

const createVerificationChallenge = async ({ email, purpose, payload }) => {
  const code = generateCode();
  const tokenHash = hashToken(code);
  const expiryDate = new Date(Date.now() + TOKEN_EXPIRY_MINUTES * 60 * 1000);

  await authSecurityModel.expireActiveChallenges(email, purpose);
  await authSecurityModel.createChallenge({
    email,
    purpose,
    tokenHash,
    payloadJson: payload ? JSON.stringify(payload) : null,
    expiresAt: expiryDate
  });

  return {
    code,
    expiresAt: expiryDate.toISOString()
  };
};

const consumeVerificationChallenge = async ({ email, purpose, token }) => {
  const tokenHash = hashToken(token);
  const challenge = await authSecurityModel.consumeChallenge({
    email,
    purpose,
    tokenHash
  });

  if (!challenge) {
    return null;
  }

  return {
    ...challenge,
    payload: challenge.Payload_JSON ? JSON.parse(challenge.Payload_JSON) : null
  };
};

const getRecentVerificationChallenge = async ({ email, purpose }) => {
  return authSecurityModel.getRecentChallenge({ email, purpose });
};

module.exports = {
  createVerificationChallenge,
  consumeVerificationChallenge,
  getRecentVerificationChallenge
};
