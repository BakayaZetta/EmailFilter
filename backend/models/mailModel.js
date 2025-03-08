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

const updateMailStatus = async (id, status) => {
    await db.query('UPDATE Mail SET Statut = ? WHERE ID_Mail = ?', [status, id]);
}

module.exports = {
    getMails,
    getMailById,
    getMailsByUserId,
    updateMailStatus,
};