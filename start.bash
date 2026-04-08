#!/bin/bash

set -e

mkdir -p src

if [ ! -d "src/tinyproxy" ]; then
    git clone https://github.com/game-hipe/amneziawg-tinyproxy.git src/tinyproxy
else
    (cd src/tinyproxy && git pull)
fi

if [ ! -d "src/manga-day" ]; then
    git clone https://github.com/game-hipe/manga-day.git src/manga-day
else
    (cd src/manga-day && git pull)
fi

if [ ! -f api.env ]; then
    echo "API Env file not found. Please create a .env file with the necessary environment variables."
    exit 1
fi

if [ ! -f bot.env ]; then
    echo "BOT Env file not found. Please create a .env file with the necessary environment variables."
    exit 1
fi

if [ ! -f config.yaml ]; then
    echo "Config file not found. Please create a config.yaml file with the necessary configuration."
    exit 1
fi

if [ ! -f tinyproxy.conf ]; then
    echo "Tinyproxy config file not found. Please create a tinyproxy.conf file with the necessary configuration."
    exit 1
fi

echo "Building Docker images..."
docker-compose build --no-cache || { echo "Docker build failed"; exit 1; }

echo "Starting services..."
docker-compose up -d || { echo "Docker up failed"; exit 1; }

echo "Services started successfully!"
