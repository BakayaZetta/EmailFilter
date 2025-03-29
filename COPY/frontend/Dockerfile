FROM node:22-alpine AS build-stage

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy environment file first (this is the key fix)
# COPY .env* ./

# Set environment variables for build
ENV FRONTEND_PORT=8000 \
    JWT_SECRET=your_secure_random_string_here \
    VITE_API_URL=/api

# Copy application code
COPY . .

# Fix: Import fs in vite.config.js if it's not there yet
RUN if ! grep -q "import fs from" vite.config.js; then \
      sed -i '1s/^/import fs from "node:fs";\n/' vite.config.js; \
    fi

# Build the app
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine AS production-stage

# Copy built files from the build-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]