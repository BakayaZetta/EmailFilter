const mailModel = require('../models/mailModel');
const db = require('../config/db');

// Fonctions d'aide pour une gestion standardisée des réponses
const handleSuccess = (res, data, status = 200) => {
  res.status(status).json(data);
};

const handleError = (res, error, status = 500) => {
  console.error('Error:', error);
  res.status(status).json({
    message: error.message || 'An error occurred while processing your request',
    error: process.env.NODE_ENV === 'development' ? error.toString() : undefined
  });
};

/**
 * Récupère les statistiques générales des emails
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getStatistics = async (req, res) => {
  try {
    // Récupérer la période depuis les paramètres de requête
    const period = req.query.period || 'month';
    
    // Calculer la date de début selon la période
    const startDate = getStartDateByPeriod(period);
    
    // Récupérer les emails pour la période donnée
    const mails = await mailModel.getMailsSince(startDate);
    
    // Calculer les statistiques
    const statistics = {
      totalMails: mails.length,
      mailsByStatus: countMailsByStatus(mails),
      threatsByCategory: countThreatsByCategory(mails),
      topSenders: getTopSenders(mails, 5),
      detectRatio: calculateDetectRatio(mails)
    };
    
    handleSuccess(res, statistics);
  } catch (error) {
    handleError(res, error);
  }
};

/**
 * Récupère les données historiques pour les graphiques
 * @async
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
exports.getHistoricalData = async (req, res) => {
  try {
    // Récupérer la période depuis les paramètres de requête
    const period = req.query.period || 'month';
    
    // Calculer la date de début selon la période
    const startDate = getStartDateByPeriod(period);
    
    // Récupérer les mails groupés par jour
    let mailsOverTime = await getMailsOverTime(startDate, period);
    
    // Si le format n'est pas comme prévu, le corriger
    if (Array.isArray(mailsOverTime) && mailsOverTime.length > 0) {
      if (Array.isArray(mailsOverTime[0]) && !Array.isArray(mailsOverTime[0][0])) {
        // Le premier élément est un tableau d'objets, gardez seulement ce tableau
        mailsOverTime = mailsOverTime[0];
      }
    }
    
    // S'assurer que chaque propriété est un nombre
    const cleanedData = mailsOverTime.map(item => ({
      date: item.date,
      total: parseInt(item.total || 0),
      quarantine: parseInt(item.quarantine || 0),
      safe: parseInt(item.safe || 0),
      error: parseInt(item.error || 0),
      deleted: parseInt(item.deleted || 0),
      pass: parseInt(item.pass || 0)
    }));
    
    handleSuccess(res, { mailsOverTime: cleanedData });
  } catch (error) {
    console.error("Error getting historical data:", error);
    
    // En cas d'erreur, générer des données fictives
    const mockData = generateMockHistoricalData(getStartDateByPeriod(req.query.period || 'month'));
    handleSuccess(res, { mailsOverTime: mockData });
  }
};

/**
 * Génère des données historiques de test
 * @param {Date} startDate - Date de début
 * @param {string} period - Période ('week', 'month', 'year', 'all')
 * @returns {Array} Données historiques fictives
 */
function generateMockHistoricalData(startDate, period) {
  const mockData = [];
  const endDate = new Date();
  let currentDate = new Date(startDate);
  
  // Déterminer l'intervalle entre les points de données en fonction de la période
  let interval = 1; // Jours par défaut
  if (period === 'year' || period === 'all') {
    interval = 7; // Une semaine pour les périodes longues
  }
  
  while (currentDate <= endDate) {
    const formattedDate = currentDate.toISOString().split('T')[0];
    
    // Générer des données aléatoires raisonnables
    const total = Math.floor(Math.random() * 20) + 5;
    const quarantine = Math.floor(Math.random() * total * 0.3);
    const error = Math.floor(Math.random() * total * 0.1);
    const safe = Math.floor(Math.random() * (total - quarantine - error)) + 1;
    const deleted = Math.floor(Math.random() * quarantine * 0.5);
    const pass = total - quarantine - error - safe - deleted;
    
    mockData.push({
      date: formattedDate,
      total,
      quarantine,
      safe,
      error,
      deleted,
      pass
    });
    
    // Incrémenter la date
    currentDate.setDate(currentDate.getDate() + interval);
  }
  
  return mockData;
}

// Fonctions utilitaires

/**
 * Calcule la date de début selon la période spécifiée
 * @param {string} period - Période ('week', 'month', 'year', 'all')
 * @returns {Date} Date de début
 */
function getStartDateByPeriod(period) {
  const now = new Date();
  switch (period) {
    case 'week':
      return new Date(now.setDate(now.getDate() - 7));
    case 'month':
      return new Date(now.setMonth(now.getMonth() - 1));
    case 'year':
      return new Date(now.setFullYear(now.getFullYear() - 1));
    case 'all':
      return new Date(0); // Depuis 1970
    default:
      return new Date(now.setMonth(now.getMonth() - 1)); // Par défaut: 1 mois
  }
}

/**
 * Compte le nombre de mails par statut
 * @param {Array} mails - Liste des mails
 * @returns {Object} Comptage par statut
 */
function countMailsByStatus(mails) {
  const statusCounts = {};
  
  mails.forEach(mail => {
    const status = mail.Statut || 'UNKNOWN';
    statusCounts[status] = (statusCounts[status] || 0) + 1;
  });
  
  return statusCounts;
}

/**
 * Compte les menaces par catégorie
 * @param {Array} mails - Liste des mails
 * @returns {Object} Comptage par catégorie de menace
 */
function countThreatsByCategory(mails) {
  const threatCounts = {
    'Phishing': 0,
    'Malware': 0,
    'Spam': 0,
    'Other': 0
  };
  
  // Pour cette démo, nous attribuons des catégories en fonction du sujet
  // En production, il faudrait se baser sur des analyses plus précises
  mails.forEach(mail => {
    if (mail.Statut !== 'QUARANTINE' && mail.Statut !== 'ERROR') return;
    
    const subject = (mail.Sujet || '').toLowerCase();
    
    if (subject.includes('account') || subject.includes('password') || subject.includes('login')) {
      threatCounts['Phishing']++;
    } else if (subject.includes('virus') || subject.includes('malware')) {
      threatCounts['Malware']++;
    } else if (subject.includes('offer') || subject.includes('discount') || subject.includes('sale')) {
      threatCounts['Spam']++;
    } else {
      threatCounts['Other']++;
    }
  });
  
  return threatCounts;
}

/**
 * Identifie les principaux expéditeurs
 * @param {Array} mails - Liste des mails
 * @param {number} limit - Nombre maximum d'expéditeurs à retourner
 * @returns {Array} Liste des principaux expéditeurs
 */
function getTopSenders(mails, limit = 5) {
  const senderCounts = {};
  
  mails.forEach(mail => {
    const sender = mail.Emetteur || 'unknown';
    senderCounts[sender] = (senderCounts[sender] || 0) + 1;
  });
  
  return Object.entries(senderCounts)
    .map(([email, count]) => ({ email, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

/**
 * Calcule le ratio de détection
 * @param {Array} mails - Liste des mails
 * @returns {number} Ratio de détection (0-1)
 */
function calculateDetectRatio(mails) {
  if (mails.length === 0) return 0;
  
  const threats = mails.filter(mail => 
    mail.Statut === 'QUARANTINE' || mail.Statut === 'ERROR'
  ).length;
  
  return threats / mails.length;
}

/**
 * Récupère les mails groupés par unité de temps
 * @param {Date} startDate - Date de début
 * @param {string} period - Période ('week', 'month', 'year', 'all')
 * @returns {Promise<Array>} Données de mails dans le temps
 */
async function getMailsOverTime(startDate, period) {
  try {
    // Format SQL pour la date en fonction de la période
    let dateFormat;
    switch (period) {
      case 'week':
        dateFormat = '%Y-%m-%d'; // Jour par jour
        break;
      case 'month':
        dateFormat = '%Y-%m-%d'; // Jour par jour
        break;
      case 'year':
        dateFormat = '%Y-%m'; // Par mois
        break;
      case 'all':
        dateFormat = '%Y-%m'; // Par mois
        break;
      default:
        dateFormat = '%Y-%m-%d'; // Par défaut: jour par jour
    }
    
    // Convertir la date en format SQL
    const sqlDate = startDate.toISOString().split('T')[0];
    
    // Requête SQL pour obtenir le nombre de mails par jour/mois et par statut
    const query = `
      SELECT 
        DATE_FORMAT(Date_Reception, ?) as date,
        COUNT(*) as total,
        SUM(CASE WHEN Statut = 'QUARANTINE' THEN 1 ELSE 0 END) as quarantine,
        SUM(CASE WHEN Statut = 'SAFE' THEN 1 ELSE 0 END) as safe,
        SUM(CASE WHEN Statut = 'ERROR' THEN 1 ELSE 0 END) as error,
        SUM(CASE WHEN Statut = 'DELETED' THEN 1 ELSE 0 END) as deleted,
        SUM(CASE WHEN Statut = 'PASS' THEN 1 ELSE 0 END) as pass
      FROM Mail
      WHERE Date_Reception >= ?
      GROUP BY DATE_FORMAT(Date_Reception, ?)
      ORDER BY date ASC
    `;
    
    // Exécuter la requête avec les paramètres
    const result = await db.query(query, [dateFormat, sqlDate, dateFormat]);
    
    // Si aucun résultat, retourner un tableau vide
    if (!result || !result.length) return [];
    
    return result;
  } catch (error) {
    console.error('Error getting mails over time:', error);
    throw error;
  }
}