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
const requestLogger = require('./middleware/logger');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(requestLogger);

app.use('/api', userRoutes);
app.use('/api/mails', mailRoutes); // Changed from '/api' to '/api/mails'
app.use('/api', analysisRoutes);
app.use('/api/statistics', statisticsRoutes);
app.use('/api', filterRulesRoutes); // Nouvelle ligne

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

// Verfy the access to the environment variables
console.log("------------------");
console.log(process.env.DB_HOST);
console.log(process.env.DB_USER);
console.log(process.env.DB_PASSWORD);
console.log(process.env.DB_NAME);
console.log(process.env.DB_PORT);
console.log(process.env.PORT);
console.log("------------------");

// Export the app
module.exports = app;
