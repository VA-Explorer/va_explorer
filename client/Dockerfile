# Build Stage
FROM node:14.0.0-slim as build-stage
RUN mkdir /app && chown -R node:node /app
WORKDIR /app
USER node
COPY package*.json ./
RUN npm install
COPY --chown=node:node ../compose/Vue .
RUN npm run build

#Production Server
FROM nginx:1.17.10-alpine
EXPOSE 80
COPY --from=build-stage /app/dist /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]
