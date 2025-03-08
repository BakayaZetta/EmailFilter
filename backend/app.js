const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const userRoutes = require('./routes/userRoutes');
const mailRoutes = require('./routes/mailRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());

app.use('/api', userRoutes);
app.use('/api', mailRoutes);

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});


// Verfy the access to the environment variables
// console.log("------------------");
// console.log(process.env.DB_HOST);
// console.log(process.env.DB_USER);
// console.log(process.env.DB_PASSWORD);
// console.log(process.env.DB_NAME);
// console.log(process.env.DB_PORT);
// console.log("------------------");
