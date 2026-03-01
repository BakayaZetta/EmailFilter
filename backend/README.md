# Detectish Backend API

A backend service for the Detectish application that provides APIs for user management, email analysis, and phishing detection.

## Prerequisites

- Node.js (we tested on v22.14.0)
- MySQL Server (docker image mysql:8.0)
- npm or yarn (npm 10.9.2)

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd detectish/backend
```

2. Install dependencies
```bash
npm install
```

3. Configure environment variables (see Environment Configuration section)

4. Start the server
```bash
node app.js
```

## Environment Configuration

Create a .env file in the root directory (detectish/) of the project with the following variables:

```
PORT=3000
DB_HOST=localhost
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name

DB_PORT=3306
FRONTEND_PORT=5173
```

## Project Structure

```
backend/
├── config/
│   └── db.js                 # Database configuration
├── controllers/
│   ├── analysisController.js # Handles analysis-related requests
│   ├── mailController.js     # Handles mail-related requests
│   └── userController.js     # Handles user-related requests
├── models/
│   ├── analysisModel.js      # Database operations for analyses
│   ├── mailModel.js          # Database operations for mails
│   └── userModel.js          # Database operations for users
├── routes/
│   ├── analysisRoutes.js     # API routes for analyses
│   ├── mailRoutes.js         # API routes for mails
│   └── userRoutes.js         # API routes for users
├── app.js                    # Application entry point
├── package.json              # Project dependencies
└── README.md                 # Project documentation
```

## API Endpoints

### User Endpoints

- `GET /api/users` - Get all users
- `GET /api/users/:id` - Get a specific user by ID

### Mail Endpoints

- `GET /api/mails` - Get all mails
- `GET /api/mails/:id` - Get a specific mail by ID
- `GET /api/mails/user/:userId` - Get all mails for a specific user
- `PUT /api/mails/:id` - Update mail status

### Analysis Endpoints

- `GET /api/analysis` - Get all analyses
- `GET /api/analysis/:id` - Get a specific analysis by ID

## Technologies Used

- **Express.js**: Web application framework
- **MySQL2**: MySQL client for Node.js
- **Dotenv**: Environment variable management
- **CORS**: Cross-Origin Resource Sharing middleware
- **Body-parser**: Request body parsing middleware

## Development

### Running in Development Mode

```bash
# Start the server
node app.js

# You can also use nodemon for automatic restarts during development
# npm install -g nodemon
# nodemon app.js
```

### One-time Blacklist Ownership Backfill

If your existing `Blacklist` rows were created before multi-tenant ownership was introduced, run this migration once:

```bash
npm run migrate:blacklist-owner
```

Optional (recommended for strict targeting): set `BLACKLIST_OWNER_ADMIN_EMAIL` in your environment before running migration to force assignment to a specific admin account.

```bash
BLACKLIST_OWNER_ADMIN_EMAIL=admin@example.com npm run migrate:blacklist-owner
```