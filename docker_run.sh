#!/bin/bash

# Start only selenium service
docker compose up -d selenium

# Wait for 10 seconds
sleep 10

# Now start macro-berlin-termin service
docker compose up -d macro-berlin-termin