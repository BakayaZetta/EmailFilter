const db = require('../config/db');

let schemaEnsured = false;

const ensureSchema = async () => {
  if (schemaEnsured) {
    return;
  }

  await db.query(`
    CREATE TABLE IF NOT EXISTS VerificationChallenge (
      ID_Challenge INT AUTO_INCREMENT PRIMARY KEY,
      Email VARCHAR(255) NOT NULL,
      Purpose VARCHAR(50) NOT NULL,
      Token_Hash VARCHAR(128) NOT NULL,
      Payload_JSON TEXT NULL,
      Expires_At DATETIME NOT NULL,
      Last_Sent_At DATETIME NOT NULL,
      Consumed_At DATETIME NULL,
      Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_verification_email_purpose (Email, Purpose),
      INDEX idx_verification_expiry (Expires_At)
    )
  `);

  await db.query(`
    CREATE TABLE IF NOT EXISTS Auth_Audit_Log (
      ID_Audit INT AUTO_INCREMENT PRIMARY KEY,
      ID_Utilisateur INT NULL,
      Email VARCHAR(255) NULL,
      Event_Type VARCHAR(100) NOT NULL,
      IP_Address VARCHAR(100) NULL,
      User_Agent VARCHAR(255) NULL,
      Detail TEXT NULL,
      Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_auth_audit_email (Email),
      INDEX idx_auth_audit_event (Event_Type)
    )
  `);

  schemaEnsured = true;
};

const expireActiveChallenges = async (email, purpose) => {
  await ensureSchema();
  await db.query(
    `UPDATE VerificationChallenge
     SET Consumed_At = NOW()
     WHERE Email = ? AND Purpose = ? AND Consumed_At IS NULL AND Expires_At > NOW()`,
    [email, purpose]
  );
};

const createChallenge = async ({ email, purpose, tokenHash, payloadJson, expiresAt }) => {
  await ensureSchema();
  const [result] = await db.query(
    `INSERT INTO VerificationChallenge (Email, Purpose, Token_Hash, Payload_JSON, Expires_At, Last_Sent_At)
     VALUES (?, ?, ?, ?, ?, NOW())`,
    [email, purpose, tokenHash, payloadJson || null, expiresAt]
  );

  return result.insertId;
};

const consumeChallenge = async ({ email, purpose, tokenHash }) => {
  await ensureSchema();

  const [rows] = await db.query(
    `SELECT *
     FROM VerificationChallenge
     WHERE Email = ?
       AND Purpose = ?
       AND Token_Hash = ?
       AND Consumed_At IS NULL
       AND Expires_At > NOW()
     ORDER BY ID_Challenge DESC
     LIMIT 1`,
    [email, purpose, tokenHash]
  );

  if (!rows.length) {
    return null;
  }

  const challenge = rows[0];
  await db.query(
    'UPDATE VerificationChallenge SET Consumed_At = NOW() WHERE ID_Challenge = ?',
    [challenge.ID_Challenge]
  );

  return challenge;
};

const getRecentChallenge = async ({ email, purpose }) => {
  await ensureSchema();
  const [rows] = await db.query(
    `SELECT *
     FROM VerificationChallenge
     WHERE Email = ? AND Purpose = ?
     ORDER BY ID_Challenge DESC
     LIMIT 1`,
    [email, purpose]
  );

  return rows[0] || null;
};

const logAuthEvent = async ({ userId = null, email = null, eventType, ipAddress = null, userAgent = null, detail = null }) => {
  await ensureSchema();
  await db.query(
    `INSERT INTO Auth_Audit_Log (ID_Utilisateur, Email, Event_Type, IP_Address, User_Agent, Detail)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [userId, email, eventType, ipAddress, userAgent, detail]
  );
};

module.exports = {
  ensureSchema,
  expireActiveChallenges,
  createChallenge,
  consumeChallenge,
  getRecentChallenge,
  logAuthEvent
};
