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

