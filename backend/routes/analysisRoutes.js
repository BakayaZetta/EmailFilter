const express = require('express');
const router = express.Router();
const analysisController = require('../controllers/analysisController');

router.get('/analysis', analysisController.getAnalysis);
router.get('/analysis/:id', analysisController.getAnalysisById);

module.exports = router;