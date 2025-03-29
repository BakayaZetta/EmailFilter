const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');

// Configurer dotenv
try {
  require('dotenv').config({ path: path.resolve(__dirname, '.env') });
} catch (err) {
  console.log('No .env file found, using environment variables from Docker');
}

const userRoutes = require('./routes/userRoutes');
const mailRoutes = require('./routes/mailRoutes');
const analysisRoutes = require('./routes/analysisRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());

// Route de diagnostic
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', message: 'Server is running' });
});

// Montage des routes d'API - ATTENTION AU PREFIX
app.use('/api', userRoutes);
app.use('/api/mails', mailRoutes);
app.use('/api', analysisRoutes);

// Log des routes disponibles au démarrage (pour débogage)
console.log('Available routes:');
app._router.stack.forEach(r => {
  if (r.route && r.route.path) {
    console.log(`${Object.keys(r.route.methods)} ${r.route.path}`);
  } else if (r.name === 'router') {
    r.handle.stack.forEach(layer => {
      if (layer.route) {
        const methods = Object.keys(layer.route.methods).join(',');
        // Trouver le chemin de base
        let basePath = '';
        app._router.stack.forEach(middleware => {
          if (middleware.name === 'router' && middleware.handle === r.handle) {
            basePath = middleware.regexp.toString().split('?')[1].slice(0, -3).replace(/\\\//g, '/');
          }
        });
        console.log(`${methods} ${basePath}${layer.route.path}`);
      }
    });
  }
});

// Ajouter cette route avant app.listen()

// Route directe pour tester si l'API est accessible sans passer par les routeurs
app.get('/api/direct-test', (req, res) => {
  res.status(200).json({ 
    message: "Direct API route works", 
    apiPrefix: "This route uses /api prefix directly"
  });
});

app.get('/direct-test', (req, res) => {
  res.status(200).json({ 
    message: "Root route works", 
    apiPrefix: "This route doesn't use /api prefix"
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Backend server running on port ${PORT}`);
});

// Verfy the access to the environment variables
console.log("------------------");
console.log(process.env.DB_HOST);
console.log(process.env.DB_USER);
console.log(process.env.DB_PASSWORD);
console.log(process.env.DB_NAME);
console.log(process.env.DB_PORT);
console.log("------------------");
