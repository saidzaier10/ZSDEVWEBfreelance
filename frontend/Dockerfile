# ---- Build stage ----
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY . .
RUN npm run build

# ---- Production stage ----
FROM nginx:alpine AS production

# Copier le build Vite vers Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier la config Nginx spécifique au SPA (gestion du routing Vue)
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
