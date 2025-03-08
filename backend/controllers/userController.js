/**
 * User Controller Module
 * Handles HTTP requests related to user resources
 * @module controllers/userController
 */

const userModel = require('../models/userModel');

/**
 * Retrieves all users
 * @async
 * @function getUsers
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @returns {Object} JSON response with user data or error message
 */
exports.getUsers = async (req, res) => {
    try {
        const users = await userModel.getUsers();
        res.status(200).json(users);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

/**
 * Retrieves a user by ID
 * @async
 * @function getUserById
 * @param {Object} req - Express request object
 * @param {Object} req.params - Request parameters
 * @param {string} req.params.id - User ID to retrieve
 * @param {Object} res - Express response object
 * @returns {Object} JSON response with user data or error message
 */
exports.getUserById = async (req, res) => {
    try {
        const user = await userModel.getUserById(req.params.id);
        if (user.length === 0) {
            res.status(404).json({ message: 'User not found' });
        } else {
            res.status(200).json(user);
        }
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};