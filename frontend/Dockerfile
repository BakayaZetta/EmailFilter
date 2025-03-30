FROM node:18-alpine AS build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy the built app to Nginx server
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add health check endpoint
RUN mkdir -p /usr/share/nginx/html/frontend-health && \
    echo '{"status":"ok"}' > /usr/share/nginx/html/frontend-health/index.json

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]