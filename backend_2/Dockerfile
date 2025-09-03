FROM node:18-alpine

WORKDIR /app
COPY . .

RUN npm install && npm run build

ENV PORT=8080
ENV GOOGLE_APPLICATION_CREDENTIALS="/secrets/google/financial-education-463317-6241fc3d93b3.json"

CMD ["node", "dist/server.js"]
