const db = require('../config/db');

/**
 * Exécute une requête SQL avec gestion d'erreur
 * @param {string} query - Requête SQL
 * @param {Array} params - Paramètres de la requête
 * @returns {Promise<Array>} Résultats de la requête
 */
const executeQuery = async (query, params = []) => {
    try {
        const [rows] = await db.query(query, params);
        return rows;
    } catch (error) {
        console.error('Database query error:', error);
        throw new Error(`Database error: ${error.message}`);
    }
};

/**
 * Récupère tous les mails
 * @returns {Promise<Array>} Liste des mails
 */
const getMails = async () => {
    return executeQuery('SELECT * FROM Mail ORDER BY Date_Reception DESC');
};

/**
 * Récupère un mail par son ID
 * @param {number} id - ID du mail
 * @returns {Promise<Object>} Le mail trouvé ou null
 */
const getMailById = async (id) => {
    const rows = await executeQuery('SELECT * FROM Mail WHERE ID_Mail = ?', [id]);
    return rows.length > 0 ? rows[0] : null;
};

/**
 * Récupère les mails d'un utilisateur
 * @param {number} userId - ID de l'utilisateur
 * @returns {Promise<Array>} Liste des mails de l'utilisateur
 */
const getMailsByUserId = async (userId) => {
    return executeQuery(
        'SELECT * FROM Mail WHERE ID_Utilisateur = ? ORDER BY Date_Reception DESC',
        [userId]
    );
};

/**
 * Récupère les mails par statut
 * @param {Array<string>} statusList - Liste des statuts
 * @returns {Promise<Array>} Liste des mails correspondants
 */
const getMailsByStatus = async (statusList) => {
    if (!statusList || statusList.length === 0) {
        return [];
    }
    const placeholders = statusList.map(() => '?').join(', ');
    return executeQuery(
        `SELECT * FROM Mail WHERE Statut IN (${placeholders}) ORDER BY Date_Reception DESC`, 
        statusList
    );
};

/**
 * Récupère les mails par utilisateur et statut
 * @param {number} userId - ID de l'utilisateur
 * @param {Array<string>} statusList - Liste des statuts
 * @returns {Promise<Array>} Liste des mails correspondants
 */
const getMailsByUserIdAndStatus = async (userId, statusList) => {
    if (!statusList || statusList.length === 0) {
        return [];
    }
    const placeholders = statusList.map(() => '?').join(', ');
    const params = [...statusList, userId];
    return executeQuery(
        `SELECT * FROM Mail WHERE Statut IN (${placeholders}) AND ID_Utilisateur = ? ORDER BY Date_Reception DESC`, 
        params
    );
};

/**
 * Met à jour le statut d'un mail
 * @param {number} id - ID du mail
 * @param {string} status - Nouveau statut
 * @returns {Promise<void>}
 */
const updateMailStatus = async (id, status) => {
    await executeQuery('UPDATE Mail SET Statut = ? WHERE ID_Mail = ?', [status, id]);
};

/**
 * Récupère un mail avec toutes ses informations associées
 * @param {number} id - ID du mail
 * @returns {Promise<Object>} Mail avec informations complètes
 */
const getMailCompleteById = async (id) => {
    // Récupérer les informations de base du mail avec les détails de l'utilisateur
    const mailResults = await executeQuery(
        `SELECT 
            m.*, 
            u.Email
         FROM Mail m 
         LEFT JOIN Utilisateur u ON m.ID_Utilisateur = u.ID_Utilisateur 
         WHERE m.ID_Mail = ?`, 
        [id]
    );
    
    if (mailResults.length === 0) {
        return null;
    }
    
    const mail = mailResults[0];
    
    // Récupération parallèle des données associées pour optimiser les performances
    const [analyses, attachments, links] = await Promise.all([
        executeQuery('SELECT * FROM Analyse WHERE ID_Mail = ? ORDER BY Type_Analyse, Date_Analyse DESC', [id]),
        executeQuery('SELECT * FROM Piece_Jointe WHERE ID_Mail = ?', [id]),
        executeQuery('SELECT * FROM Lien WHERE ID_Mail = ?', [id])
    ]);
    
    // Construction de l'objet résultat
    return {
        id: mail.ID_Mail,
        subject: mail.Sujet,
        content: mail.Contenu,
        receivedDate: mail.Date_Reception,
        sender: mail.Emetteur,
        status: mail.Statut,
        user: {
            id: mail.ID_Utilisateur,
            email: mail.Email,
        },
        analyses: analyses.map(analysis => ({
            id: analysis.ID_Analyse,
            result: analysis.Resultat_Analyse,
            date: analysis.Date_Analyse,
            type: analysis.Type_Analyse
        })),
        attachments: attachments.map(attachment => ({
            id: attachment.ID_Piece_Jointe,
            name: attachment.Nom_Fichier,
            type: attachment.Type_Fichier,
            size: attachment.Taille_Fichier,
            status: attachment.Statut_Analyse
        })),
        links: links.map(link => ({
            id: link.ID_Lien,
            url: link.URL,
            status: link.Statut_Analyse
        }))
    };
};

module.exports = {
    getMails,
    getMailById,
    getMailsByUserId,
    updateMailStatus,
    getMailsByStatus,
    getMailsByUserIdAndStatus,
    getMailCompleteById
};