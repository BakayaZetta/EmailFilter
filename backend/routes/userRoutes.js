const express = require('express');
const router = express.Router();
const { body } = require('express-validator');
const userController = require('../controllers/userController');

// Authentication routes
router.post('/auth/register', [
    // Input validation
    body('firstName').trim().isLength({ min: 2 }).escape(),
    body('lastName').trim().isLength({ min: 2 }).escape(),
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 })
], userController.register);

router.post('/auth/login', [
    // Input validation
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, }),
    body('password').notEmpty()
], userController.login);

// User data routes
router.get('/users', userController.getUsers);
router.get('/users/:id', userController.getUserById);

module.exports = router;