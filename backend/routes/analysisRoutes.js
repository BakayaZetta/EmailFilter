const express = require('express');
const router = express.Router();
const analysisController = require('../controllers/analysisController');
const auth = require('../middleware/auth');

router.use(auth);

router.get('/analysis', analysisController.getAnalysis);
router.get('/analysis/:id', analysisController.getAnalysisById);
router.get('/analysis/mail/:mailId', analysisController.getAnalysisByMailId);

module.exports = router;