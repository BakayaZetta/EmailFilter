const db = require('../config/db');

const getMails = async () => {
    const [rows] = await db.query('SELECT * FROM Mail');
    return rows;
};

const getMailById = async (id) => {
    const [rows] = await db.query('SELECT * FROM Mail WHERE id = ?', [id]);
    return rows;
}

const getMailsByUserId = async (userId) => {
    const [rows] = await db.query('SELECT * FROM Mail WHERE userId = ?', [userId]);
    return rows;
}

const updateMailStatus = async (id, status) => {
    await db.query('UPDATE Mail SET status = ? WHERE id = ?', [status, id]);
}

module.exports = {
    getMails,
    getMailById,
    getMailsByUserId,
    updateMailStatus,
};