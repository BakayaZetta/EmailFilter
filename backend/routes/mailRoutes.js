const express = require('express');
const router = express.Router();
const mailController = require('../controllers/mailController');

// Regroupement des routes par fonctionnalité
// Routes de base pour les mails
router.get('/', mailController.getMails);
router.get('/status', mailController.getMailsByStatus);
router.get('/:id', mailController.getMailById);
router.get('/:id/complete', mailController.getMailCompleteById);

// Routes spécifiques à l'utilisateur
router.get('/user/:userId', mailController.getMailsByUserId);
router.get('/user/:userId/status', mailController.getMailsByUserIdAndStatus);

// Routes de mise à jour
router.put('/:id/status', mailController.updateMailStatus);

// Routes pour le téléchargement
router.post('/upload', mailController.uploadEmail);

module.exports = router;