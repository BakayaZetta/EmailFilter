const mailModel = require('../models/mailModel');

exports.getMails = async (req, res) => {
    try {
        const mails = await mailModel.getMails();
        res.status(200).json(mails);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.getMailById = async (req, res) => {
    try {
        const mail = await mailModel.getMailById(req.params.id);
        if (mail.length === 0) {
            res.status(404).json({ message: 'Mail not found' });
        } else {
            res.status(200).json(mail);
        }
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

exports.getMailsByUserId = async (req, res) => {
    try {
        const mails = await mailModel.getMailsByUserId(req.params.userId);
        if (mails.length === 0) {
            res.status(404).json({ message: 'Mail not found' });
        } else {
            res.status(200).json(mails);
        }
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
}

exports.updateMailStatus = async (req, res) => {
    try {
        await mailModel.updateMailStatus(req.params.id, req.body.status);
        res.status(204).end();
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// Nouvelle fonction pour récupérer les mails par statut
exports.getMailsByStatus = async (req, res) => {
    try {
        const statusList = req.query.status ? req.query.status.split(',') : ['QUARANTINE', 'ERROR'];
        const mails = await mailModel.getMailsByStatus(statusList);
        res.status(200).json(mails);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// Nouvelle fonction pour récupérer les mails d'un utilisateur par statut
exports.getMailsByUserIdAndStatus = async (req, res) => {
    try {
        const userId = req.params.userId;
        const statusList = req.query.status ? req.query.status.split(',') : ['QUARANTINE', 'ERROR'];
        const mails = await mailModel.getMailsByUserIdAndStatus(userId, statusList);
        res.status(200).json(mails);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

