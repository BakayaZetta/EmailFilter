const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const userRoutes = require('./routes/userRoutes');
const mailRoutes = require('./routes/mailRoutes');
const analysisRoutes = require('./routes/analysisRoutes');
const statisticsRoutes = require('./routes/statisticsRoutes');
const filterRulesRoutes = require('./routes/filterRulesRoutes'); // Nouvelle ligne
const adminRoutes = require('./routes/adminRoutes');
const requestLogger = require('./middleware/logger');

const app = express();
const PORT = process.env.PORT || 3000;

const parseAllowedOrigins = () => {
  const rawOrigins = process.env.CORS_ALLOWED_ORIGINS || '';
  const parsed = rawOrigins
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);

  if (parsed.length > 0) {
    return parsed;
  }

  return ['http://localhost', 'http://localhost:80', 'http://localhost:3000'];
};

const allowedOrigins = parseAllowedOrigins();
const corsOptions = {
  origin: (origin, callback) => {
    if (!origin) {
      return callback(null, true);
    }

    if (allowedOrigins.includes(origin)) {
      return callback(null, true);
    }

    return callback(new Error('CORS policy violation'));
  },
  credentials: true,
};

app.use(cors(corsOptions));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(requestLogger);

app.use('/api', userRoutes);
app.use('/api/mails', mailRoutes); // Changed from '/api' to '/api/mails'
app.use('/api', analysisRoutes);
app.use('/api/statistics', statisticsRoutes);
app.use('/api', filterRulesRoutes); // Nouvelle ligne
app.use('/api/admin', adminRoutes);

// Health check endpoint
app.get('/backend-health', (req, res) => {
  res.status(200).json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.use((req, res) => {
  console.warn(
    `[WARN] [${new Date().toISOString()}] Not Found - ${req.method} ${req.originalUrl}`
  );
  res.status(404).json({ message: 'Route not found' });
});

app.use((err, req, res, next) => {
  console.error(
    `[ERROR] [${new Date().toISOString()}] ${req.method} ${req.originalUrl} - ${err.message}`
  );
  if (err.stack) {
    console.error(err.stack);
  }
  res.status(500).json({ message: 'Something broke!' });
});

process.on('unhandledRejection', (reason) => {
  console.error(`[ERROR] [${new Date().toISOString()}] Unhandled Rejection`, reason);
});

process.on('uncaughtException', (error) => {
  console.error(`[ERROR] [${new Date().toISOString()}] Uncaught Exception`, error);
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

// Export the app
module.exports = app;
