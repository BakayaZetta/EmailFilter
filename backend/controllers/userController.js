/**
 * User Controller Module
 * Handles HTTP requests related to user resources
 */

const userModel = require('../models/userModel');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { validationResult } = require('express-validator');

exports.getUsers = async (req, res) => {
    try {
        const users = await userModel.getUsers();
        res.status(200).json(users);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

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

exports.register = async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const { firstName, lastName, email, password } = req.body;

    try {
        const existingUser = await userModel.getUserByEmail(email);
        if (existingUser) {
            // Pre-created accounts (by email ingestion) have an empty password —
            // allow completing registration by setting a real password.
            if (!existingUser.Mot_de_passe) {
                const hashedPassword = await bcrypt.hash(password, 10);
                await userModel.completeRegistration(existingUser.ID_Utilisateur, { firstName, lastName, hashedPassword });
                const token = jwt.sign(
                    { userId: existingUser.ID_Utilisateur, email: existingUser.Email, role: existingUser.Role },
                    process.env.JWT_SECRET,
                    { expiresIn: '24h' }
                );
                return res.status(200).json({
                    user: {
                        id: existingUser.ID_Utilisateur,
                        firstName,
                        lastName,
                        email: existingUser.Email,
                        role: existingUser.Role
                    },
                    token
                });
            }
            return res.status(409).json({ message: 'User already exists with this email' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        const newUser = await userModel.createUser({ firstName, lastName, email, hashedPassword });

        const token = jwt.sign(
            { userId: newUser.id, email: newUser.email, role: newUser.role },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.status(201).json({
            user: {
                id: newUser.id,
                firstName: newUser.firstName,
                lastName: newUser.lastName,
                email: newUser.email,
                role: newUser.role
            },
            token
        });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.login = async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const { email, password } = req.body;

    try {
        const user = await userModel.getUserByEmail(email);

        console.log('User retrieved from database:', {
            id: user?.ID_Utilisateur,
            email: user?.Email,
            hasPasswordField: !!user?.Mot_de_passe
        });

        if (!user) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        // Pre-created accounts (no password yet) cannot log in until registration is completed
        if (!user.Mot_de_passe) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        const passwordMatch = await bcrypt.compare(password, user.Mot_de_passe);
        if (!passwordMatch) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }

        const token = jwt.sign(
            { userId: user.ID_Utilisateur, email: user.Email, role: user.Role },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.status(200).json({
            user: {
                id: user.ID_Utilisateur,
                firstName: user.Prenom,
                lastName: user.Nom,
                email: user.Email,
                role: user.Role
            },
            token
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: error.message });
    }
};
