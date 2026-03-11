const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');

router.use(auth);
router.use(adminAuth);

router.get('/users', adminController.getUsers);
router.get('/users/:id/profile', adminController.getUserProfile);
router.post('/users', adminController.createUser);
router.put('/users/:id/role', adminController.updateUserRole);
router.put('/users/:id/deactivate', adminController.deactivateUser);
router.get('/logs', adminController.getLogs);
router.get('/scans', adminController.getScans);

module.exports = router;
