#!/bin/bash
set -euo pipefail

# Generate a persistant cookie for JupyterHub
echo "Checking for a JupyterHub cookie secret..."
if [ ! -f /etc/jupyterhub/cookie_secret ]; then
    echo "Initializing a new cookie secret"
    mkdir -p /etc/jupyterhub
    openssl rand -base64 2048 > /etc/jupyterhub/cookie_secret
    chmod 600 /etc/jupyterhub/cookie_secret
fi

echo "Initialization Complete - Staring JupyterHub"
exec jupyterhub --no-ssl -f /srv/jupyterhub/jupyterhub_config.py
