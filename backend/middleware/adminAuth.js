const ADMIN_ROLES = new Set(['admin', 'super_admin', 'superadmin']);

module.exports = (req, res, next) => {
  const role = (req.userData?.role || '').toLowerCase();

  if (!ADMIN_ROLES.has(role)) {
    return res.status(403).json({ message: 'Administrator access required' });
  }

  next();
};
