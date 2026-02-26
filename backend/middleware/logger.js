const requestLogger = (req, res, next) => {
  const startTime = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const now = new Date().toISOString();
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown';
    const baseMessage = `[${now}] ${req.method} ${req.originalUrl} ${res.statusCode} - ${duration}ms - ${ip}`;

    if (res.statusCode >= 500) {
      console.error(`[ERROR] ${baseMessage}`);
      return;
    }

    if (res.statusCode >= 400) {
      console.warn(`[WARN] ${baseMessage}`);
      return;
    }

    console.log(`[INFO] ${baseMessage}`);
  });

  next();
};

module.exports = requestLogger;
