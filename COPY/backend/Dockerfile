FROM node:22-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Create .env file at startup if needed
ENV PORT=3000 \
    JWT_SECRET=your_secret_key_change_in_production

EXPOSE 3000

CMD ["node", "app.js"]