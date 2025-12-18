# Build Stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Serve Stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Custom Nginx config to handle React Router and Proxy to Backend
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8020
CMD ["nginx", "-g", "daemon off;"]
