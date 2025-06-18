#!/bin/bash
# CC_AUTOMATOR4 Dependency Setup Script
set -e  # Exit on any error

echo "Validating API keys..."
if [ -z "${OPENAI_API_KEY}" ]; then
  echo "ERROR: OPENAI_API_KEY environment variable not set"
  exit 1
fi

echo "Starting Docker services..."
docker-compose up -d

echo "Waiting for services to be ready..."
until docker exec chroma echo "ok"; do
  echo "Waiting for service to be ready..."
  sleep 2
done

echo "All dependencies validated successfully!"