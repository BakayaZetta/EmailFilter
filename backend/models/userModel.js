/**
 * User model module
 * This file contains functions for accessing user data in the database.
 * @module models/userModel
 */

const db = require('../config/db');
let userAuditColumnsEnsured = false;

const ensureUserAuditColumns = async () => {
    if (userAuditColumnsEnsured) {
        return;
    }

    const [createdCol] = await db.query("SHOW COLUMNS FROM Utilisateur LIKE 'created_at'");
    if (createdCol.length === 0) {
        await db.query(
            'ALTER TABLE Utilisateur ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'
        );
    }

    const [lastLoginCol] = await db.query("SHOW COLUMNS FROM Utilisateur LIKE 'last_login_at'");
    if (lastLoginCol.length === 0) {
        await db.query('ALTER TABLE Utilisateur ADD COLUMN last_login_at DATETIME NULL');
    }

    const [failedAttemptsCol] = await db.query("SHOW COLUMNS FROM Utilisateur LIKE 'failed_login_attempts'");
    if (failedAttemptsCol.length === 0) {
        await db.query('ALTER TABLE Utilisateur ADD COLUMN failed_login_attempts INT NOT NULL DEFAULT 0');
    }

    const [lockoutCol] = await db.query("SHOW COLUMNS FROM Utilisateur LIKE 'lockout_until'");
    if (lockoutCol.length === 0) {
        await db.query('ALTER TABLE Utilisateur ADD COLUMN lockout_until DATETIME NULL');
    }

    const [trustCol] = await db.query("SHOW COLUMNS FROM Utilisateur LIKE 'verification_trust_until'");
    if (trustCol.length === 0) {
        await db.query('ALTER TABLE Utilisateur ADD COLUMN verification_trust_until DATETIME NULL');
    }

    userAuditColumnsEnsured = true;
};

/**
 * Retrieves all users from the database
 * @async
 * @function getUsers
 * @returns {Promise<Array>} A promise that resolves with an array of user objects
 */
const getUsers = async () => {
    await ensureUserAuditColumns();
    const [rows] = await db.query('SELECT * FROM Utilisateur');
    return rows;
};

/**
 * Retrieves a user by their ID
 * @async
 * @function getUserById
 * @param {number} id - The ID of the user to retrieve
 * @returns {Promise<Array>} A promise that resolves with an array containing the found user
 */
const getUserById = async (id) => {
    await ensureUserAuditColumns();
    // ATTENTION: Vulnérable aux injections SQL
    // const [rows] = await db.query(`SELECT * FROM Utilisateur WHERE id = ${id}`);
    // Il faudrait utiliser des requêtes paramétrées comme ceci:
    const [rows] = await db.query('SELECT * FROM Utilisateur WHERE ID_Utilisateur = ?', [id]);
    return rows;
};

/**
 * Retrieves a user by their email
 * @async
 * @function getUserByEmail
 * @param {string} email - The email of the user to retrieve
 * @returns {Promise<Object|null>} A promise that resolves with the user object or null if not found
 */
const getUserByEmail = async (email) => {
    await ensureUserAuditColumns();
    const [rows] = await db.query('SELECT * FROM Utilisateur WHERE Email = ?', [email]);
    return rows.length > 0 ? rows[0] : null;
};

/**
 * Creates a new user in the database
 * @async
 * @function createUser
 * @param {Object} user - The user information
 * @param {string} user.firstName - User's first name
 * @param {string} user.lastName - User's last name
 * @param {string} user.email - User's email address
 * @param {string} user.hashedPassword - Hashed password
 * @returns {Promise<Object>} A promise that resolves with the created user information
 */
const createUser = async ({ firstName, lastName, email, hashedPassword }) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        'INSERT INTO Utilisateur (Prenom, Nom, Email, Mot_de_passe, Role) VALUES (?, ?, ?, ?, ?)',
        [firstName, lastName, email, hashedPassword, 'user']
    );
    
    return {
        id: result.insertId,
        firstName,
        lastName,
        email,
        role: 'user'
    };
};

const createUserWithRole = async ({ firstName, lastName, email, hashedPassword, role }) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        'INSERT INTO Utilisateur (Prenom, Nom, Email, Mot_de_passe, Role) VALUES (?, ?, ?, ?, ?)',
        [firstName, lastName, email, hashedPassword, role]
    );

    return {
        id: result.insertId,
        firstName,
        lastName,
        email,
        role
    };
};

const getUsersForAdmin = async () => {
    await ensureUserAuditColumns();
    const [rows] = await db.query(
        `SELECT ID_Utilisateur, Prenom, Nom, Email, Role, created_at, last_login_at
         FROM Utilisateur
         ORDER BY ID_Utilisateur DESC`
    );
    return rows;
};

const updateUserRole = async (id, role) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        'UPDATE Utilisateur SET Role = ? WHERE ID_Utilisateur = ?',
        [role, id]
    );
    return result.affectedRows > 0;
};

const deactivateUser = async (id) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        "UPDATE Utilisateur SET Role = 'disabled' WHERE ID_Utilisateur = ?",
        [id]
    );
    return result.affectedRows > 0;
};

const updateLastLoginById = async (id) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        'UPDATE Utilisateur SET last_login_at = NOW() WHERE ID_Utilisateur = ?',
        [id]
    );
    return result.affectedRows > 0;
};

const incrementFailedLoginAttempt = async (id, lockoutThreshold, lockoutMinutes) => {
    await ensureUserAuditColumns();
    await db.query(
        `UPDATE Utilisateur
         SET failed_login_attempts = failed_login_attempts + 1,
             lockout_until = CASE
               WHEN failed_login_attempts + 1 >= ?
               THEN DATE_ADD(NOW(), INTERVAL ? MINUTE)
               ELSE lockout_until
             END
         WHERE ID_Utilisateur = ?`,
        [lockoutThreshold, lockoutMinutes, id]
    );

    const [rows] = await db.query(
        'SELECT failed_login_attempts, lockout_until FROM Utilisateur WHERE ID_Utilisateur = ?',
        [id]
    );
    return rows[0] || null;
};

const resetFailedLoginAttempts = async (id) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        'UPDATE Utilisateur SET failed_login_attempts = 0, lockout_until = NULL WHERE ID_Utilisateur = ?',
        [id]
    );
    return result.affectedRows > 0;
};

const setVerificationTrust = async (id, trustDays) => {
    await ensureUserAuditColumns();
    const [result] = await db.query(
        'UPDATE Utilisateur SET verification_trust_until = DATE_ADD(NOW(), INTERVAL ? DAY) WHERE ID_Utilisateur = ?',
        [trustDays, id]
    );
    return result.affectedRows > 0;
};

const getUserProfileForAdmin = async (id) => {
    await ensureUserAuditColumns();

    const [rows] = await db.query(
        `SELECT
            u.ID_Utilisateur,
            u.Prenom,
            u.Nom,
            u.Email,
            u.Role,
            u.created_at,
            u.last_login_at,
            COUNT(m.ID_Mail) AS scan_count,
            MAX(m.Date_Reception) AS last_scan_at
         FROM Utilisateur u
         LEFT JOIN Mail m ON m.ID_Utilisateur = u.ID_Utilisateur
         WHERE u.ID_Utilisateur = ?
         GROUP BY u.ID_Utilisateur, u.Prenom, u.Nom, u.Email, u.Role, u.created_at, u.last_login_at`,
        [id]
    );

    return rows.length > 0 ? rows[0] : null;
};

const completeRegistration = async (userId, { firstName, lastName, hashedPassword }) => {
    const [result] = await db.query(
        'UPDATE Utilisateur SET Prenom = ?, Nom = ?, Mot_de_passe = ? WHERE ID_Utilisateur = ?',
        [firstName, lastName, hashedPassword, userId]
    );
    return result.affectedRows > 0;
};

module.exports = {
    getUsers,
    getUserById,
    getUserByEmail,
    createUser,
    createUserWithRole,
    getUsersForAdmin,
    updateUserRole,
    deactivateUser,
    updateLastLoginById,
    getUserProfileForAdmin,
    incrementFailedLoginAttempt,
    resetFailedLoginAttempts,
    setVerificationTrust,
    completeRegistration
};