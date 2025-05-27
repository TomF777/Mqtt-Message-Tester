#!bin/bash

echo "Creating docker network for the project "
docker network create NetworkMqttTester

echo "Up docker compose "
docker compose -f compose.yml up -d
