/**
 * Authentication middleware
 * Verifies JWT tokens for protected routes
 * @module middleware/auth
 */

const jwt = require('jsonwebtoken');

/**
 * Middleware to verify authentication token
 * @function auth
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
module.exports = (req, res, next) => {
    try {
        // Get token from header
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ message: 'Authentication required' });
        }
        
        const token = authHeader.split(' ')[1];
        
        // Verify token
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        // Add user data to request
        req.userData = {
            userId: decoded.userId,
            email: decoded.email,
            role: decoded.role || 'user'
        };
        next();
    } catch (error) {
        return res.status(401).json({ message: 'Authentication failed' });
    }
};