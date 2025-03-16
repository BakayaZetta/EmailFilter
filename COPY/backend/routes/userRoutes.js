const express = require('express');
const router = express.Router();
const { body } = require('express-validator');
const userController = require('../controllers/userController');

// Authentication routes
router.post('/auth/register', [
    // Input validation
    body('firstName').trim().isLength({ min: 2 }).escape(),
    body('lastName').trim().isLength({ min: 2 }).escape(),
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('password').isLength({ min: 6 })
], userController.register);

// Ajouter une route de test pour vérifier que le routeur fonctionne
router.get('/auth/test', (req, res) => {
    res.status(200).json({ message: "Authentication routes are working" });
  });

router.post('/auth/login', [
    // Input validation
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('password').notEmpty()
], userController.login);

// User data routes
router.get('/users', userController.getUsers);
router.get('/users/:id', userController.getUserById);

module.exports = router;