const db = require('../config/db');

const getMails = async () => {
    const [rows] = await db.query('SELECT * FROM Mail');
    return rows;
};

const getMailById = async (id) => {
    const [rows] = await db.query('SELECT * FROM Mail WHERE ID_Mail = ?', [id]);
    return rows;
}

const getMailsByUserId = async (userId) => {
    const [rows] = await db.query('SELECT * FROM Mail WHERE ID_Utilisateur = ?', [userId]);
    return rows;
}

// Nouvelle fonction pour récupérer les mails par statut
const getMailsByStatus = async (statusList) => {
    // Utiliser une requête paramétrée avec placeholders pour chaque statut
    const placeholders = statusList.map(() => '?').join(', ');
    const [rows] = await db.query(`SELECT * FROM Mail WHERE Statut IN (${placeholders}) ORDER BY Date_Reception DESC`, statusList);
    return rows;
}

// Nouvelle fonction pour récupérer les mails par statut pour un utilisateur spécifique
const getMailsByUserIdAndStatus = async (userId, statusList) => {
    // Utiliser une requête paramétrée avec placeholders pour chaque statut
    const placeholders = statusList.map(() => '?').join(', ');
    const params = [...statusList, userId];
    const [rows] = await db.query(
        `SELECT * FROM Mail WHERE Statut IN (${placeholders}) AND ID_Utilisateur = ? ORDER BY Date_Reception DESC`, 
        params
    );
    return rows;
}

const updateMailStatus = async (id, status) => {
    await db.query('UPDATE Mail SET Statut = ? WHERE ID_Mail = ?', [status, id]);
}

module.exports = {
    getMails,
    getMailById,
    getMailsByUserId,
    updateMailStatus,
    getMailsByStatus,
    getMailsByUserIdAndStatus
};