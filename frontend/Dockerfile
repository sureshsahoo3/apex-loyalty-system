# ── Stage 1: Build ──────────────────────────────────────────────────
FROM node:24-alpine AS build

WORKDIR /app

# Install dependencies (cached layer)
COPY package*.json ./
RUN npm ci --silent

# Copy source
COPY . .

# Inject backend API URL at build time (replaced by deploy script)
ARG API_URL=http://localhost:8080
RUN sed -i "s|BACKEND_API_URL|${API_URL}|g" src/environments/environment.prod.ts

# Production build
RUN npx ng build --configuration production

# ── Stage 2: Serve ───────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
