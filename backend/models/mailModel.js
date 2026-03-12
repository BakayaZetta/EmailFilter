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
    return executeQuery('SELECT ID_Mail, Sujet, Emetteur, Destinataire, ID_Utilisateur, Date_Reception, Statut FROM Mail ORDER BY Date_Reception DESC');
};

/**
 * Récupère les scans en file d'attente
 * @param {number} limit - Nombre maximum de lignes
 * @returns {Promise<Array>} Liste des scans en attente
 */
const getQueuedMails = async (limit = 100) => {
    const safeLimit = Math.min(500, Math.max(1, Number(limit) || 100));

    return executeQuery(
        `SELECT
            ID_Mail,
            Sujet,
            Emetteur,
            Destinataire,
            ID_Utilisateur,
            Date_Reception,
            Statut,
            TIMESTAMPDIFF(MINUTE, Date_Reception, NOW()) AS queued_minutes
         FROM Mail
         WHERE Statut = 'Analyse_pending'
         ORDER BY Date_Reception DESC
         LIMIT ?`,
        [safeLimit]
    );
};

const clearQueuedMails = async () => {
    return executeQuery(
        `UPDATE Mail
         SET Statut = 'ERROR'
         WHERE Statut = 'Analyse_pending'`
    );
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
        'SELECT ID_Mail, Sujet, Emetteur, Destinataire, ID_Utilisateur, Date_Reception, Statut FROM Mail WHERE ID_Utilisateur = ? ORDER BY Date_Reception DESC',
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
        `SELECT ${MAIL_LIST_COLUMNS}
         FROM Mail m
         WHERE m.Statut IN (${placeholders}) 
         ORDER BY m.Date_Reception DESC`, 
        statusList
    );
};

const getMailsByStatusPaginated = async (statusList, page = 1, limit = 50) => {
    if (!statusList || statusList.length === 0) {
        return [];
    }

    const safePage = Math.max(1, Number(page) || 1);
    const safeLimit = Math.min(200, Math.max(1, Number(limit) || 50));
    const offset = (safePage - 1) * safeLimit;
    const placeholders = statusList.map(() => '?').join(', ');

    return executeQuery(
        `SELECT ${MAIL_LIST_COLUMNS}
         FROM Mail m
         WHERE m.Statut IN (${placeholders})
         ORDER BY m.Date_Reception DESC
         LIMIT ? OFFSET ?`,
        [...statusList, safeLimit, offset]
    );
};

const countMailsByStatus = async (statusList) => {
    if (!statusList || statusList.length === 0) {
        return 0;
    }

    const placeholders = statusList.map(() => '?').join(', ');
    const rows = await executeQuery(
        `SELECT COUNT(*) as total
         FROM Mail m
         WHERE m.Statut IN (${placeholders})`,
        statusList
    );

    return rows[0]?.total || 0;
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
        `SELECT ID_Mail, Sujet, Emetteur, Destinataire, ID_Utilisateur, Date_Reception, Statut
         FROM Mail
         WHERE Statut IN (${placeholders}) AND ID_Utilisateur = ?
         ORDER BY Date_Reception DESC`, 
        params
    );
};

const getMailsByUserIdAndStatusPaginated = async (userId, statusList, page = 1, limit = 50) => {
    if (!statusList || statusList.length === 0) {
        return [];
    }

    const safePage = Math.max(1, Number(page) || 1);
    const safeLimit = Math.min(200, Math.max(1, Number(limit) || 50));
    const offset = (safePage - 1) * safeLimit;
    const placeholders = statusList.map(() => '?').join(', ');

    return executeQuery(
        `SELECT ID_Mail, Sujet, Emetteur, Destinataire, ID_Utilisateur, Date_Reception, Statut
         FROM Mail
         WHERE Statut IN (${placeholders}) AND ID_Utilisateur = ?
         ORDER BY Date_Reception DESC
         LIMIT ? OFFSET ?`,
        [...statusList, userId, safeLimit, offset]
    );
};

const countMailsByUserIdAndStatus = async (userId, statusList) => {
    if (!statusList || statusList.length === 0) {
        return 0;
    }

    const placeholders = statusList.map(() => '?').join(', ');
    const rows = await executeQuery(
        `SELECT COUNT(*) as total
         FROM Mail
         WHERE Statut IN (${placeholders}) AND ID_Utilisateur = ?`,
        [...statusList, userId]
    );

    return rows[0]?.total || 0;
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
        recipient: mail.Destinataire,
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

/**
 * Récupère les mails depuis une date spécifique
 * @param {Date} startDate - Date de début
 * @returns {Promise<Array>} Liste des mails
 */
const getMailsSince = async (startDate) => {
  const sqlDate = startDate.toISOString().split('T')[0];
  
  return executeQuery(
      `SELECT ID_Mail, Sujet, Emetteur, Destinataire, ID_Utilisateur, Date_Reception, Statut FROM Mail 
     WHERE Date_Reception >= ? 
     ORDER BY Date_Reception DESC`,
    [sqlDate]
  );
};

/**
 * Saves a new email to the database
 * @param {Object} emailData - The email data to save
 * @returns {Promise<Object>} The saved email
 */
const saveEmail = async (emailData) => {
    const { subject, content, sender, recipient, userId, receivedDate } = emailData;

    const result = await executeQuery(
        `INSERT INTO Mail (Sujet, Contenu, Emetteur, Destinataire, ID_Utilisateur, Date_Reception)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [subject, content, sender, recipient, userId, receivedDate]
    );

    return {
        id: result.insertId,
        subject,
        content,
        sender,
        recipient,
        userId,
        receivedDate,
    };
};

module.exports = {
    getMails,
    getQueuedMails,
    clearQueuedMails,
    getMailById,
    getMailsByUserId,
    updateMailStatus,
    getMailsByStatus,
    getMailsByStatusPaginated,
    countMailsByStatus,
    getMailsByUserIdAndStatus,
    getMailsByUserIdAndStatusPaginated,
    countMailsByUserIdAndStatus,
    getMailCompleteById,
    getMailsSince,
    saveEmail
};

const MAIL_LIST_COLUMNS = `
    m.ID_Mail,
    m.Sujet,
    m.Emetteur,
    m.Destinataire,
    m.ID_Utilisateur,
    m.Date_Reception,
    m.Statut
`;