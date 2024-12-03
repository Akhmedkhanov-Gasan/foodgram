FROM node:18
WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build
RUN npm install --global http-server

EXPOSE 80

CMD ["http-server", "-p", "80", "/app/build"]
