const db = require('../config/db');

const getAnalysis = async () => {
    const [rows] = await db.query('SELECT * FROM Analyse');
    return rows;
};

const getAnalysisById = async (id) => {
    const [rows] = await db.query('SELECT * FROM Analyse WHERE ID_Analyse = ?', [id]);
    return rows;
}

// Nouvelle fonction pour récupérer les analyses d'un mail spécifique
const getAnalysisByMailId = async (mailId) => {
    const [rows] = await db.query('SELECT * FROM Analyse WHERE ID_Mail = ? ORDER BY Type_Analyse', [mailId]);
    return rows;
}

module.exports = {
    getAnalysis,
    getAnalysisById,
    getAnalysisByMailId
};