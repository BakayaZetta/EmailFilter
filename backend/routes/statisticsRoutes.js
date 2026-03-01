const express = require('express');
const router = express.Router();
const statisticsController = require('../controllers/statisticsController');
const auth = require('../middleware/auth');

router.use(auth);

// Routes des statistiques
router.get('/', statisticsController.getStatistics);
router.get('/history', statisticsController.getHistoricalData);

module.exports = router;