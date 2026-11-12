FROM node:25-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate && pnpm install --frozen-lockfile
COPY . .
ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}
RUN pnpm run build

FROM nginx:1.31.8-alpine3.24
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY nginx-entrypoint.sh /usr/local/bin/casework-nginx-entrypoint.sh
RUN apk upgrade --no-cache \
    && chmod +x /usr/local/bin/casework-nginx-entrypoint.sh
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
ENTRYPOINT ["/usr/local/bin/casework-nginx-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
