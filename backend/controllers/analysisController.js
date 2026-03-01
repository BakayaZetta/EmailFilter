const analysisModel = require('../models/analysisModel');
const ADMIN_ROLES = new Set(['admin', 'super_admin', 'superadmin']);
const isAdminUser = (req) => ADMIN_ROLES.has((req.userData?.role || '').toLowerCase());

exports.getAnalysis = async (req, res) => {
    try {
        const analysis = await analysisModel.getAnalysis(req.userData.userId, isAdminUser(req));
        res.status(200).json(analysis);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.getAnalysisById = async (req, res) => {
    try {
        const analysis = await analysisModel.getAnalysisById(
            req.params.id,
            req.userData.userId,
            isAdminUser(req)
        );
        if (analysis.length === 0) {
            res.status(404).json({ message: 'Analysis not found' });
        } else {
            res.status(200).json(analysis);
        }
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// Nouvelle fonction pour récupérer les analyses d'un mail spécifique
exports.getAnalysisByMailId = async (req, res) => {
    try {
        const analysis = await analysisModel.getAnalysisByMailId(
            req.params.mailId,
            req.userData.userId,
            isAdminUser(req)
        );
        res.status(200).json(analysis);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};