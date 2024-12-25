FROM node:22 as build

WORKDIR /app

RUN npm i -g pnpm
RUN pnpm install

COPY ../pnpm-lock.yaml /app
COPY package.json  /app

COPY . .

RUN pnpm run build
RUN pnpm prune --prod

FROM node:22-alpine AS deployer

WORKDIR /app

COPY --from=builder /app/build build/
COPY --from=builder /app/package.json .

EXPOSE 3000

ENV NODE_ENV=production

CMD [ "node", "build" ]