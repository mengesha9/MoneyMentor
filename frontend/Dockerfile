# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Accept build-time env vars
ARG VITE_BACKEND
ARG VITE_BACKEND_TWO

# Set env vars so they can be used in the .env file
ENV VITE_BACKEND=${VITE_BACKEND}
ENV VITE_BACKEND_TWO=${VITE_BACKEND_TWO}

# Create the .env file BEFORE copying source files
RUN echo "VITE_BACKEND=$VITE_BACKEND" > .env && \
    echo "VITE_BACKEND_TWO=$VITE_BACKEND_TWO" >> .env

# Now copy source files
COPY . .

# Install dependencies
RUN npm ci

# Build with .env already in place
RUN npm run build

# Serve using nginx
FROM nginx:alpine

# Copy build output to nginx html dir
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
