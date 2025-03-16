/**
 * User Controller Module
 * Handles HTTP requests related to user resources
 * @module controllers/userController
 */

const userModel = require('../models/userModel');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { validationResult } = require('express-validator');

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

/**
 * Register a new user
 * @async
 * @function register
 * @param {Object} req - Express request object
 * @param {Object} req.body - Request body containing user information
 * @param {Object} res - Express response object
 * @returns {Object} JSON response with user data or error message
 */
exports.register = async (req, res) => {
    // Validate request data
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    const { firstName, lastName, email, password } = req.body;
    
    try {
        // Check if user already exists
        const existingUser = await userModel.getUserByEmail(email);
        if (existingUser) {
            return res.status(409).json({ message: 'User already exists with this email' });
        }
        
        // Hash the password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);
        
        // Create user
        const newUser = await userModel.createUser({
            firstName,
            lastName,
            email,
            hashedPassword
        });
        
        // Generate JWT token
        const token = jwt.sign(
            { userId: newUser.id, email: newUser.email },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );
        
        // Return user info (without password) and token
        res.status(201).json({
            user: {
                id: newUser.id,
                firstName: newUser.firstName,
                lastName: newUser.lastName,
                email: newUser.email
            },
            token
        });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

/**
 * Login an existing user
 * @async
 * @function login
 * @param {Object} req - Express request object
 * @param {Object} req.body - Request body containing login credentials
 * @param {Object} res - Express response object
 * @returns {Object} JSON response with user data and authentication token
 */
exports.login = async (req, res) => {
    // Validate request data
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    const { email, password } = req.body;
    
    try {
        // Find user by email
        const user = await userModel.getUserByEmail(email);
        
        // DEBUG: Ajoutez un log de débogage pour voir l'objet utilisateur
        console.log('User retrieved from database:', {
            id: user?.ID_Utilisateur,
            email: user?.Email,
            hasPasswordField: !!user?.Mot_de_passe
        });
        
        if (!user) {
            // Use vague message for security (don't reveal whether email exists)
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Compare password with stored hash - CORRECTION ICI
        const passwordMatch = await bcrypt.compare(password, user.Mot_de_passe);
        if (!passwordMatch) {
            // Use vague message for security
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Generate JWT token
        const token = jwt.sign(
            { userId: user.ID_Utilisateur, email: user.Email },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );
        
        // Return user info and token
        res.status(200).json({
            user: {
                id: user.ID_Utilisateur,
                firstName: user.Prenom,
                lastName: user.Nom,
                email: user.Email
            },
            token
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: error.message });
    }
};