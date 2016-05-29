#!/bin/sh
set -euo pipefail

# Wait for nginx as our Let's Encrypt challenge is served by it
echo "Waiting for nginx to start..."
until $(curl --output /dev/null --silent --head --fail --insecure https://$DOMAIN); do
    printf '.'
    sleep 5
done
echo ""

# Generate a Let's Encrypt certificate
echo "Checking for a Let's Encrypt certificate"
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
  /generate-certificate.sh
fi

echo "Initialization Complete - Starting the Let's Encrypt cron job"
# Start CRON
exec /usr/sbin/crond -f -d 8
