const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const userRoutes = require('./routes/userRoutes');
const mailRoutes = require('./routes/mailRoutes');
const analysisRoutes = require('./routes/analysisRoutes');
const statisticsRoutes = require('./routes/statisticsRoutes');
const filterRulesRoutes = require('./routes/filterRulesRoutes'); // Nouvelle ligne

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use('/api', userRoutes);
app.use('/api/mails', mailRoutes); // Changed from '/api' to '/api/mails'
app.use('/api', analysisRoutes);
app.use('/api/statistics', statisticsRoutes);
app.use('/api', filterRulesRoutes); // Nouvelle ligne

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

// Verfy the access to the environment variables
// console.log("------------------");
// console.log(process.env.DB_HOST);
// console.log(process.env.DB_USER);
// console.log(process.env.DB_PASSWORD);
// console.log(process.env.DB_NAME);
// console.log(process.env.DB_PORT);
// console.log("------------------");

// Export the app
module.exports = app;
