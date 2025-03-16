/**
 * User model module
 * This file contains functions for accessing user data in the database.
 * @module models/userModel
 */

const db = require('../config/db');

/**
 * Retrieves all users from the database
 * @async
 * @function getUsers
 * @returns {Promise<Array>} A promise that resolves with an array of user objects
 */
const getUsers = async () => {
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
    const [result] = await db.query(
        'INSERT INTO Utilisateur (Prenom, Nom, Email, Mot_de_passe, Role) VALUES (?, ?, ?, ?, ?)',
        [firstName, lastName, email, hashedPassword, 'admin']
    );
    
    return {
        id: result.insertId,
        firstName,
        lastName,
        email
    };
};

module.exports = {
    getUsers,
    getUserById,
    getUserByEmail,
    createUser
};