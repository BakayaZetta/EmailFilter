const express = require('express');
const router = express.Router();
const mailController = require('../controllers/mailController');

router.get('/mails', mailController.getMails);
router.get('/mails/:id', mailController.getMailById);
router.get('/mails/user/:userId', mailController.getMailsByUserId);
router.put('/mails/:id', mailController.updateMailStatus);

module.exports = router;