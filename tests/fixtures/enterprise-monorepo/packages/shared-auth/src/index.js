'use strict';
const jwt = require('jsonwebtoken');

const SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';

/**
 * Validates and decodes a JWT token.
 * @param {string} token - The JWT token string.
 * @returns {object} Decoded JWT payload.
 * @throws {Error} If token is missing or invalid.
 */
function validateToken(token) {
  if (!token) throw new Error('No token provided');
  return jwt.verify(token, SECRET);
}

/**
 * Express middleware: rejects requests without a valid Bearer token.
 */
function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized: missing Bearer token' });
  }
  try {
    req.user = validateToken(authHeader.slice(7));
    next();
  } catch (err) {
    res.status(401).json({ error: `Invalid token: ${err.message}` });
  }
}

/**
 * Creates a signed JWT token.
 * @param {object} payload - Data to encode.
 * @param {string} [expiresIn='1h'] - Expiry duration string.
 * @returns {string} Signed JWT string.
 */
function createToken(payload, expiresIn = '1h') {
  return jwt.sign(payload, SECRET, { expiresIn });
}

/**
 * Checks if a user has a required role (RBAC helper).
 * @param {string[]} allowedRoles - Roles permitted for the resource.
 * @returns {Express.RequestHandler} Middleware function.
 */
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) return res.status(401).json({ error: 'Unauthorized' });
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Forbidden: insufficient role' });
    }
    next();
  };
}

module.exports = { validateToken, requireAuth, createToken, requireRole };
