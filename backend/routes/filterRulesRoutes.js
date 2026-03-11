const express = require('express');
const router = express.Router();
const filterRulesController = require('../controllers/filterRulesController');
const auth = require('../middleware/auth');

// Routes for filter rules management
router.get('/filter-rules', auth, filterRulesController.getFilterRules);
router.get('/filter-rules/:id', auth, filterRulesController.getFilterRuleById);
router.post('/filter-rules', auth, filterRulesController.createFilterRule);
router.put('/filter-rules/:id', auth, filterRulesController.updateFilterRule);
router.delete('/filter-rules/:id', auth, filterRulesController.deleteFilterRule);

module.exports = router;