const userModel = require('../models/userModel');
const mailModel = require('../models/mailModel');
const requestLogger = require('../middleware/logger');
const bcrypt = require('bcrypt');

const ALLOWED_ROLES = new Set(['user', 'admin', 'super_admin', 'disabled']);

exports.getUsers = async (req, res) => {
  try {
    const users = await userModel.getUsersForAdmin();
    res.status(200).json(users);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.updateUserRole = async (req, res) => {
  try {
    const userId = Number(req.params.id);
    const role = String(req.body.role || '').toLowerCase();

    if (!Number.isInteger(userId) || userId <= 0) {
      return res.status(400).json({ message: 'Invalid user id' });
    }

    if (!ALLOWED_ROLES.has(role)) {
      return res.status(400).json({ message: 'Invalid role' });
    }

    if (String(req.userData.userId) === String(userId) && role === 'user') {
      return res.status(400).json({ message: 'You cannot remove your own admin access' });
    }

    const exists = await userModel.getUserById(userId);
    if (!exists || exists.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    await userModel.updateUserRole(userId, role);

    const updated = await userModel.getUserById(userId);
    const user = updated[0];
    res.status(200).json({
      id: user.ID_Utilisateur,
      firstName: user.Prenom,
      lastName: user.Nom,
      email: user.Email,
      role: user.Role
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.createUser = async (req, res) => {
  try {
    const firstName = String(req.body.firstName || '').trim();
    const lastName = String(req.body.lastName || '').trim();
    const email = String(req.body.email || '').trim().toLowerCase();
    const password = String(req.body.password || '');
    const role = String(req.body.role || 'user').toLowerCase();

    if (!firstName || !lastName || !email || !password) {
      return res.status(400).json({ message: 'firstName, lastName, email and password are required' });
    }

    if (!ALLOWED_ROLES.has(role)) {
      return res.status(400).json({ message: 'Invalid role' });
    }

    const existingUser = await userModel.getUserByEmail(email);
    if (existingUser) {
      return res.status(409).json({ message: 'User already exists with this email' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const createdUser = await userModel.createUserWithRole({
      firstName,
      lastName,
      email,
      hashedPassword,
      role
    });

    return res.status(201).json(createdUser);
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.deactivateUser = async (req, res) => {
  try {
    const userId = Number(req.params.id);

    if (!Number.isInteger(userId) || userId <= 0) {
      return res.status(400).json({ message: 'Invalid user id' });
    }

    if (String(req.userData.userId) === String(userId)) {
      return res.status(400).json({ message: 'You cannot deactivate your own account' });
    }

    const existingUser = await userModel.getUserById(userId);
    if (!existingUser || existingUser.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    await userModel.deactivateUser(userId);

    return res.status(200).json({ message: 'User deactivated successfully' });
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.getUserProfile = async (req, res) => {
  try {
    const userId = Number(req.params.id);

    if (!Number.isInteger(userId) || userId <= 0) {
      return res.status(400).json({ message: 'Invalid user id' });
    }

    const profile = await userModel.getUserProfileForAdmin(userId);
    if (!profile) {
      return res.status(404).json({ message: 'User not found' });
    }

    return res.status(200).json(profile);
  } catch (error) {
    return res.status(500).json({ message: error.message });
  }
};

exports.getLogs = async (req, res) => {
  try {
    const limit = Number(req.query.limit || 200);
    const logs = requestLogger.getRecentLogs(limit);
    res.status(200).json(logs);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.getScans = async (req, res) => {
  try {
    const scans = await mailModel.getMails();
    res.status(200).json(scans);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.getQueuedScans = async (req, res) => {
  try {
    const limit = Number(req.query.limit || 100);
    const queued = await mailModel.getQueuedMails(limit);
    res.status(200).json(queued);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};
