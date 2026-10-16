# ---- build stage: compile the react app ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- runtime stage: just nginx + static files ----
# nginx-unprivileged runs as uid 101 and listens on 8080 instead of 80
FROM nginxinc/nginx-unprivileged:1.29-alpine

USER root
RUN apk upgrade --no-cache
USER 101

# BACKEND_URL is filled in by the nginx image's envsubst step at startup
ENV BACKEND_URL=http://backend:8000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
