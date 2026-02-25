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

const handleForbidden = (res, message = 'Forbidden') => {
    res.status(403).json({ message });
};

const isAdminUser = (req) => req.userData?.role === 'admin';

/**
 * Récupère tous les mails
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getMails = async (req, res) => {
    try {
        const mails = isAdminUser(req)
            ? await mailModel.getMails()
            : await mailModel.getMailsByUserId(req.userData.userId);
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
        if (!isAdminUser(req) && String(mail.ID_Utilisateur) !== String(req.userData.userId)) {
            return handleForbidden(res, 'You do not have access to this mail');
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
        if (!isAdminUser(req) && String(req.params.userId) !== String(req.userData.userId)) {
            return handleForbidden(res, 'You do not have access to these mails');
        }
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

        const mail = await mailModel.getMailById(id);
        if (!mail) {
            return handleNotFound(res, 'Mail not found');
        }
        if (!isAdminUser(req) && String(mail.ID_Utilisateur) !== String(req.userData.userId)) {
            return handleForbidden(res, 'You do not have access to update this mail');
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
        const page = Math.max(1, parseInt(req.query.page, 10) || 1);
        const limit = Math.min(200, Math.max(1, parseInt(req.query.limit, 10) || 50));

        const [mails, total] = isAdminUser(req)
            ? await Promise.all([
                mailModel.getMailsByStatusPaginated(statusList, page, limit),
                mailModel.countMailsByStatus(statusList)
            ])
            : await Promise.all([
                mailModel.getMailsByUserIdAndStatusPaginated(req.userData.userId, statusList, page, limit),
                mailModel.countMailsByUserIdAndStatus(req.userData.userId, statusList)
            ]);
        
        // Enrichir les données si nécessaire avec des informations complémentaires
        const enrichedMails = await Promise.all(mails.map(async (mail) => {
            // Si vous avez besoin d'enrichir chaque mail avec des informations sur l'utilisateur
            // Vous pourriez faire une requête supplémentaire ou optimiser avec une jointure dans le model
            return {
                ...mail,
                // Ajouter ici des données supplémentaires si nécessaire
            };
        }));
        
        handleSuccess(res, {
            data: enrichedMails,
            pagination: {
                page,
                limit,
                total,
                totalPages: Math.max(1, Math.ceil(total / limit))
            }
        });
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
        if (!isAdminUser(req) && String(userId) !== String(req.userData.userId)) {
            return handleForbidden(res, 'You do not have access to these mails');
        }
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
        if (!isAdminUser(req) && String(mail.user?.id) !== String(req.userData.userId)) {
            return handleForbidden(res, 'You do not have access to this mail');
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

        const effectiveUserId = isAdminUser(req) && userId ? userId : req.userData.userId;

        if (!subject || !content || !sender || !effectiveUserId || !receivedDate) {
            return handleError(res, new Error('All fields are required'), 400);
        }

        const newEmail = await mailModel.saveEmail({
            subject,
            content,
            sender,
            userId: effectiveUserId,
            receivedDate,
        });

        handleSuccess(res, newEmail, 201);
    } catch (error) {
        handleError(res, error);
    }
};

