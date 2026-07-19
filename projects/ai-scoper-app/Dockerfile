FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=dev

COPY . .

EXPOSE 5070

ENV PORT=5070

CMD ["node", "server.js"]
