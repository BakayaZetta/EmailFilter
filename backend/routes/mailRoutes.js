const express = require('express');
const router = express.Router();
const mailController = require('../controllers/mailController');

router.get('/mails', mailController.getMails);
router.get('/mails/:id', mailController.getMailById);
router.get('/mails/user/:userId', mailController.getMailsByUserId);
router.put('/mails/:id', mailController.updateMailStatus);

// Nouvelles routes
router.get('/mails/status/filter', mailController.getMailsByStatus);
router.get('/mails/user/:userId/status', mailController.getMailsByUserIdAndStatus);

module.exports = router;