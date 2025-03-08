const analysisModel = require('../models/analysisModel');

exports.getAnalysis = async (req, res) => {
    try {
        const analysis = await analysisModel.getAnalysis();
        res.status(200).json(analysis);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.getAnalysisById = async (req, res) => {
    try {
        const analysis = await analysisModel.getAnalysisById(req.params.id);
        if (analysis.length === 0) {
            res.status(404).json({ message: 'Analysis not found' });
        } else {
            res.status(200).json(analysis);
        }
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};