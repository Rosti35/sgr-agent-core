FROM node:22.12-alpine AS node
WORKDIR /app

COPY package.json \
     package-lock.json \
     .dockerignore \
     eslint.config.ts \
     vite.config.ts \
     tsconfig.json \
     tsconfig.app.json \
     tsconfig.node.json \
     ./

# build frontend
RUN npm ci --ignore-scripts

COPY . .

# Set the ENV variables
ARG VITE_API_BASE_URL
ARG VITE_APP_ENV=production
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_ENV=${VITE_APP_ENV}

RUN npm run build --ignore-scripts

FROM nginx:stable-alpine AS server

# Railway requires listening on $PORT
COPY nginx/default.conf /etc/nginx/conf.d/default.conf.template

# Copy the built frontend
COPY --from=node --chown=nginx /app/dist/ /usr/share/nginx/html/

# Replace PORT in nginx config at runtime and start nginx
# Railway provides PORT env var, default to 80 if not set
CMD sh -c "sed -i 's/listen\s*80;/listen ${PORT:-80};/g' /etc/nginx/conf.d/default.conf.template && \
    cp /etc/nginx/conf.d/default.conf.template /etc/nginx/conf.d/default.conf && \
    nginx -g 'daemon off;'"
