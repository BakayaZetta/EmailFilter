const mysql = require('mysql2');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const dbHost = process.env.DB_HOST || 'localhost';
const dbUser = process.env.DB_USER || process.env.MYSQL_USER;
const dbPassword = process.env.DB_PASSWORD || process.env.MYSQL_PASSWORD;
const dbName = process.env.DB_NAME || process.env.MYSQL_DATABASE;
const dbPort = Number(process.env.DB_PORT || 3306);

// Create a connection pool
const pool = mysql.createPool({
    host: dbHost,
    user: dbUser,
    password: dbPassword,
    database: dbName,
    port: dbPort,
    waitForConnections: true,
    connectionLimit: 10,
    maxIdle: 10, // The maximum number of connections waiting in the queue
    idleTimeout: 10000, // The time interval in milliseconds that a connection can be idle before being released
    queueLimit: 0, 
    enableKeepAlive: true,
    keepAliveInitialDelay: 0,
});

module.exports = pool.promise();