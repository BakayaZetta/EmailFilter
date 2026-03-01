const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../../.env') });

if (!process.env.DB_USER && process.env.MYSQL_USER) {
  process.env.DB_USER = process.env.MYSQL_USER;
}
if (!process.env.DB_PASSWORD && process.env.MYSQL_PASSWORD) {
  process.env.DB_PASSWORD = process.env.MYSQL_PASSWORD;
}
if (!process.env.DB_NAME && process.env.MYSQL_DATABASE) {
  process.env.DB_NAME = process.env.MYSQL_DATABASE;
}

const db = require('../../config/db');

const ADMIN_ROLES = ['admin', 'super_admin', 'superadmin'];

async function ensureBlacklistOwnerColumn() {
  const [columns] = await db.query("SHOW COLUMNS FROM Blacklist LIKE 'ID_Utilisateur'");

  if (columns.length === 0) {
    await db.query('ALTER TABLE Blacklist ADD COLUMN ID_Utilisateur INT NULL');
    await db.query('CREATE INDEX idx_blacklist_user ON Blacklist (ID_Utilisateur)');
  }
}

async function resolveAdminUserId() {
  const adminEmail = process.env.BLACKLIST_OWNER_ADMIN_EMAIL;

  if (adminEmail) {
    const [users] = await db.query(
      'SELECT ID_Utilisateur, Role FROM Utilisateur WHERE Email = ? LIMIT 1',
      [adminEmail]
    );

    if (users.length === 0) {
      throw new Error(`No user found for BLACKLIST_OWNER_ADMIN_EMAIL=${adminEmail}`);
    }

    const role = String(users[0].Role || '').toLowerCase();
    if (!ADMIN_ROLES.includes(role)) {
      throw new Error(`User ${adminEmail} is not an admin (role=${users[0].Role})`);
    }

    return users[0].ID_Utilisateur;
  }

  const rolePlaceholders = ADMIN_ROLES.map(() => '?').join(', ');
  const [admins] = await db.query(
    `SELECT ID_Utilisateur FROM Utilisateur WHERE LOWER(Role) IN (${rolePlaceholders}) ORDER BY ID_Utilisateur ASC LIMIT 1`,
    ADMIN_ROLES
  );

  if (admins.length === 0) {
    throw new Error('No admin user found. Set BLACKLIST_OWNER_ADMIN_EMAIL to a valid admin email.');
  }

  return admins[0].ID_Utilisateur;
}

async function backfillBlacklistOwner() {
  await ensureBlacklistOwnerColumn();

  const adminUserId = await resolveAdminUserId();

  const [result] = await db.query(
    'UPDATE Blacklist SET ID_Utilisateur = ? WHERE ID_Utilisateur IS NULL',
    [adminUserId]
  );

  console.log(`[MIGRATION] Blacklist owner backfill completed. Updated rows: ${result.affectedRows}`);
  console.log(`[MIGRATION] Assigned owner ID_Utilisateur=${adminUserId}`);
}

backfillBlacklistOwner()
  .then(async () => {
    await db.end();
    process.exit(0);
  })
  .catch(async (error) => {
    console.error('[MIGRATION] Failed:', error.message);
    try {
      await db.end();
    } catch (_) {
      // ignore connection close errors
    }
    process.exit(1);
  });
