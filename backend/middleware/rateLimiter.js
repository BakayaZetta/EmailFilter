const buckets = new Map();

const createRateLimiter = ({ windowMs, max, keyPrefix }) => {
  return (req, res, next) => {
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown';
    const bucketKey = `${keyPrefix}:${ip}`;
    const now = Date.now();

    const entries = buckets.get(bucketKey) || [];
    const validEntries = entries.filter((timestamp) => now - timestamp < windowMs);

    if (validEntries.length >= max) {
      return res.status(429).json({
        message: 'Too many requests. Please try again later.'
      });
    }

    validEntries.push(now);
    buckets.set(bucketKey, validEntries);
    return next();
  };
};

module.exports = {
  createRateLimiter
};
