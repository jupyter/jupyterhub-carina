#!/bin/sh
set -euo pipefail

echo "Generating a Let's Encrypt certificate for $DOMAIN..."
if [ "$USE_PRODUCTION" = true ]; then
  LETSENCRYPT_SERVER="https://acme-v01.api.letsencrypt.org/directory"
else
  echo "Using the Let's Encrypt staging server"
  LETSENCRYPT_SERVER="https://acme-staging.api.letsencrypt.org/directory"
fi

docker run --rm \
  --volumes-from jupyterhub-data \
  quay.io/letsencrypt/letsencrypt certonly \
  --server $LETSENCRYPT_SERVER \
  --domain $DOMAIN \
  --authenticator webroot \
  --webroot-path /etc/letsencrypt/webrootauth/ \
  --email $EMAIL \
  --renew-by-default \
  --agree-tos

# Copy the certificate to the volume shared with nginx
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /etc/certs/jupyterhub.key
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/certs/jupyterhub.crt

# Send nginx a SIGHUP to trigger it to reload its configuration without shutting down.
echo "Reloading nginx configuration"
docker kill --signal=HUP nginx
