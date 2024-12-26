FROM node:22 as builder

WORKDIR /app

COPY pnpm-lock.yaml /app
COPY package.json  /app

RUN npm i -g pnpm
RUN pnpm install

COPY . .

RUN pnpm run build
RUN pnpm prune --prod

FROM node:22-alpine AS deployer

COPY --from=builder /app/build build/
COPY --from=builder /app/node_modules node_modules/

EXPOSE 3000
ENV NODE_ENV=production
CMD [ "node", "build" ]