const db = require('../config/db');

const getAnalysis = async (userId = null, isAdmin = false) => {
    if (isAdmin) {
        const [rows] = await db.query('SELECT * FROM Analyse');
        return rows;
    }

    const [rows] = await db.query(
        `SELECT a.*
         FROM Analyse a
         INNER JOIN Mail m ON a.ID_Mail = m.ID_Mail
         WHERE m.ID_Utilisateur = ?`,
        [userId]
    );
    return rows;
};

const getAnalysisById = async (id, userId = null, isAdmin = false) => {
    if (isAdmin) {
        const [rows] = await db.query('SELECT * FROM Analyse WHERE ID_Analyse = ?', [id]);
        return rows;
    }

    const [rows] = await db.query(
        `SELECT a.*
         FROM Analyse a
         INNER JOIN Mail m ON a.ID_Mail = m.ID_Mail
         WHERE a.ID_Analyse = ? AND m.ID_Utilisateur = ?`,
        [id, userId]
    );
    return rows;
}

// Nouvelle fonction pour récupérer les analyses d'un mail spécifique
const getAnalysisByMailId = async (mailId, userId = null, isAdmin = false) => {
    if (isAdmin) {
        const [rows] = await db.query('SELECT * FROM Analyse WHERE ID_Mail = ? ORDER BY Type_Analyse', [mailId]);
        return rows;
    }

    const [rows] = await db.query(
        `SELECT a.*
         FROM Analyse a
         INNER JOIN Mail m ON a.ID_Mail = m.ID_Mail
         WHERE a.ID_Mail = ? AND m.ID_Utilisateur = ?
         ORDER BY a.Type_Analyse`,
        [mailId, userId]
    );
    return rows;
}

module.exports = {
    getAnalysis,
    getAnalysisById,
    getAnalysisByMailId
};