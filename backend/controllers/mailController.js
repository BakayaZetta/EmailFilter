const mailModel = require('../models/mailModel');

// Fonctions d'aide pour une gestion standardisée des réponses
const handleSuccess = (res, data, status = 200) => {
    res.status(status).json(data);
};

const handleError = (res, error, status = 500) => {
    console.error('Controller error:', error);
    res.status(status).json({ message: error.message });
};

const handleNotFound = (res, message = 'Resource not found') => {
    res.status(404).json({ message });
};

/**
 * Récupère tous les mails
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMails = async (req, res) => {
    try {
        const mails = await mailModel.getMails();
        handleSuccess(res, mails);
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Récupère un mail par son ID
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMailById = async (req, res) => {
    try {
        const mail = await mailModel.getMailById(req.params.id);
        if (!mail) {
            return handleNotFound(res, 'Mail not found');
        }
        handleSuccess(res, mail);
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Récupère les mails d'un utilisateur
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMailsByUserId = async (req, res) => {
    try {
        const mails = await mailModel.getMailsByUserId(req.params.userId);
        if (!mails || mails.length === 0) {
            return handleNotFound(res, 'No mails found for this user');
        }
        handleSuccess(res, mails);
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Met à jour le statut d'un mail
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.updateMailStatus = async (req, res) => {
    try {
        const { id } = req.params;
        const { status } = req.body;
        
        if (!status) {
            return handleError(res, new Error('Status is required'), 400);
        }
        
        await mailModel.updateMailStatus(id, status);
        res.status(204).end();
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Récupère les mails par statut
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMailsByStatus = async (req, res) => {
    try {
        const statusList = req.query.status ? req.query.status.split(',') : ['QUARANTINE', 'ERROR'];
        const mails = await mailModel.getMailsByStatus(statusList);
        
        // Enrichir les données si nécessaire avec des informations complémentaires
        const enrichedMails = await Promise.all(mails.map(async (mail) => {
            // Si vous avez besoin d'enrichir chaque mail avec des informations sur l'utilisateur
            // Vous pourriez faire une requête supplémentaire ou optimiser avec une jointure dans le model
            return {
                ...mail,
                // Ajouter ici des données supplémentaires si nécessaire
            };
        }));
        
        handleSuccess(res, enrichedMails);
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Récupère les mails d'un utilisateur par statut
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMailsByUserIdAndStatus = async (req, res) => {
    try {
        const { userId } = req.params;
        const statusList = req.query.status ? req.query.status.split(',') : ['QUARANTINE', 'ERROR'];
        const mails = await mailModel.getMailsByUserIdAndStatus(userId, statusList);
        handleSuccess(res, mails);
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Récupère un mail avec toutes ses informations associées
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMailCompleteById = async (req, res) => {
    try {
        const mail = await mailModel.getMailCompleteById(req.params.id);
        
        if (!mail) {
            return handleNotFound(res, 'Mail not found');
        }
        
        handleSuccess(res, mail);
    } catch (error) {
        handleError(res, error);
    }
};

/**
 * Uploads an email and saves it to the database
 * @async
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 */
exports.uploadEmail = async (req, res) => {
    try {
        const { subject, content, sender, userId, receivedDate } = req.body;

        if (!subject || !content || !sender || !userId || !receivedDate) {
            return handleError(res, new Error('All fields are required'), 400);
        }

        const newEmail = await mailModel.saveEmail({
            subject,
            content,
            sender,
            userId,
            receivedDate,
        });

        handleSuccess(res, newEmail, 201);
    } catch (error) {
        handleError(res, error);
    }
};

