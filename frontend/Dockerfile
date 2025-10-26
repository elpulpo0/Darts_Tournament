FROM node:alpine AS builder

WORKDIR /app

ARG VITE_APP_NAME
ARG VITE_ENV
ARG VITE_PORT_BACK
ARG VITE_PRINTFUL
ARG VITE_PAYPAL_CLIENT_ID

ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_ENV=$VITE_ENV
ENV VITE_PORT_BACK=$VITE_PORT_BACK
ENV VITE_PRINTFUL=$VITE_PRINTFUL
ENV VITE_PAYPAL_CLIENT_ID=$VITE_PAYPAL_CLIENT_ID

COPY package.json package-lock.json ./

RUN npm install

COPY . .

RUN npm run build
RUN cp build-meta.json dist/

FROM node:alpine

WORKDIR /usr/share/app

RUN npm install -g serve

COPY --from=builder /app/dist .

RUN apk add --no-cache shadow bash
RUN useradd -ms /bin/bash appuser
RUN chown -R appuser:appuser /usr/share/app

USER appuser

EXPOSE 8081

CMD ["serve", "-s", "-l", "8081"]
