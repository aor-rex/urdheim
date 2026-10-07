# Urdheim web: Next.js feed + board + profiles.
# Dokploy: set NEXT_PUBLIC_API to the api service URL at build time.
FROM node:26-slim AS build
WORKDIR /web
COPY web-next/package*.json ./
RUN npm install
COPY web-next/ ./
ARG NEXT_PUBLIC_API=http://localhost:8091
ENV NEXT_PUBLIC_API=$NEXT_PUBLIC_API
RUN npm run build

FROM node:26-slim
WORKDIR /web
ENV NODE_ENV=production
COPY --from=build /web ./
EXPOSE 8092
CMD ["npm", "start"]
