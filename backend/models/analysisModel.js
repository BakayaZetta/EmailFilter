const db = require('../config/db');

const getAnalysis = async () => {
    const [rows] = await db.query('SELECT * FROM Analyse');
    return rows;
};

const getAnalysisById = async (id) => {
    const [rows] = await db.query('SELECT * FROM Analyse WHERE id = ?', [id]);
    return rows;
}

module.exports = {
    getAnalysis,
    getAnalysisById,
};