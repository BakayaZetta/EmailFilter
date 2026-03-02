const MAX_LOG_ENTRIES = 500;
const recentRequestLogs = [];

const pushLogEntry = (entry) => {
  recentRequestLogs.unshift(entry);
  if (recentRequestLogs.length > MAX_LOG_ENTRIES) {
    recentRequestLogs.pop();
  }
};

const requestLogger = (req, res, next) => {
  const startTime = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const now = new Date().toISOString();
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown';
    const baseMessage = `[${now}] ${req.method} ${req.originalUrl} ${res.statusCode} - ${duration}ms - ${ip}`;
    const level = res.statusCode >= 500 ? 'ERROR' : res.statusCode >= 400 ? 'WARN' : 'INFO';

    pushLogEntry({
      timestamp: now,
      level,
      method: req.method,
      url: req.originalUrl,
      statusCode: res.statusCode,
      duration,
      ip
    });

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

requestLogger.getRecentLogs = (limit = 100) => {
  const safeLimit = Math.min(500, Math.max(1, Number(limit) || 100));
  return recentRequestLogs.slice(0, safeLimit);
};

module.exports = requestLogger;
