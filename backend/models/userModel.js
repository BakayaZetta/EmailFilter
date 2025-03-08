/**
 * Module de modèle utilisateur
 * Ce fichier contient les fonctions d'accès aux données des utilisateurs dans la base de données.
 * @module models/userModel
 */

const db = require('../config/db');

/**
 * Récupère tous les utilisateurs de la base de données
 * @async
 * @function getUsers
 * @returns {Promise<Array>} Une promesse qui résout avec un tableau d'objets utilisateur
 */
const getUsers = async () => {
    const [rows] = await db.query('SELECT * FROM Utilisateur');
    return rows;
};

/**
 * Récupère un utilisateur par son identifiant
 * @async
 * @function getUserById
 * @param {number} id - L'identifiant de l'utilisateur à récupérer
 * @returns {Promise<Array>} Une promesse qui résout avec un tableau contenant l'utilisateur trouvé
 */
const getUserById = async (id) => {
    // ATTENTION: Vulnérable aux injections SQL
    // const [rows] = await db.query(`SELECT * FROM Utilisateur WHERE id = ${id}`);
    // Il faudrait utiliser des requêtes paramétrées comme ceci:
    const [rows] = await db.query('SELECT * FROM Utilisateur WHERE id = ?', [id]);
    return rows;
};

module.exports = {
    getUsers,
    getUserById,
};