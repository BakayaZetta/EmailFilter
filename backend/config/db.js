const mysql = require('mysql2');
const path = require('path');
require('dotenv').config();

// Create a connection pool
const pool = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    port: process.env.DB_PORT,
    waitForConnections: true,
    connectionLimit: 10,
    maxIdle: 10, // The maximum number of connections waiting in the queue
    idleTimeout: 10000, // The time interval in milliseconds that a connection can be idle before being released
    queueLimit: 0, 
    enableKeepAlive: true,
    keepAliveInitialDelay: 0,
});

module.exports = pool.promise();