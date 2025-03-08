const db = require('../config/db');

const getAnalysis = async () => {
    const [rows] = await db.query('SELECT * FROM Analyse');
    return rows;
};

const getAnalysisById = async (id) => {
    const [rows] = await db.query('SELECT * FROM Analyse WHERE ID_Analyse = ?', [id]);
    return rows;
}

module.exports = {
    getAnalysis,
    getAnalysisById,
};