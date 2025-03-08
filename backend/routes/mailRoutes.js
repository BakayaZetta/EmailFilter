const express = require('express');
const router = express.Router();
const mailController = require('../controllers/mailController');

router.get('/mails', mailController.getMails);

module.exports = router;