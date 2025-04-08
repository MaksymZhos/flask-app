#!/bin/bash
echo "Stopping services..."
docker compose down

echo "Removing Kafka meta.properties..."
rm -f ./data/kafka/meta.properties

echo "Starting services again..."
docker compose up -d
