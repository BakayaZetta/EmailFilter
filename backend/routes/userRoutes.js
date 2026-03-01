const express = require('express');
const router = express.Router();
const { body } = require('express-validator');
const userController = require('../controllers/userController');
const { createRateLimiter } = require('../middleware/rateLimiter');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

const registerRateLimit = createRateLimiter({
    keyPrefix: 'auth-register',
    windowMs: 15 * 60 * 1000,
    max: 10
});

const loginRateLimit = createRateLimiter({
    keyPrefix: 'auth-login',
    windowMs: 15 * 60 * 1000,
    max: 20
});

const resendRateLimit = createRateLimiter({
    keyPrefix: 'auth-resend',
    windowMs: 15 * 60 * 1000,
    max: 8
});

// Authentication routes
router.post('/auth/register/request-verification', registerRateLimit, [
    // Input validation
    body('firstName').trim().isLength({ min: 2 }).escape(),
    body('lastName').trim().isLength({ min: 2 }).escape(),
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('password').isLength({ min: 6 })
], userController.requestRegisterVerification);

router.post('/auth/register/verify', registerRateLimit, [
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('code').trim().isLength({ min: 4, max: 10 })
], userController.verifyAndRegister);

router.post('/auth/verification/resend', resendRateLimit, [
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('purpose').trim().isIn(['register', 'login'])
], userController.resendVerification);

router.post('/auth/login', loginRateLimit, [
    // Input validation
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('password').notEmpty()
], userController.login);

router.post('/auth/login/verify', loginRateLimit, [
    body('email').isEmail().normalizeEmail({ gmail_remove_dots: false, all_lowercase: true,}),
    body('code').trim().isLength({ min: 4, max: 10 })
], userController.verifyLogin);

// User data routes
router.get('/users', auth, adminAuth, userController.getUsers);
router.get('/users/:id', auth, adminAuth, userController.getUserById);

module.exports = router;