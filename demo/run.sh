#!/bin/bash
set -euo pipefail

# Figure out the current directory
__SCRIPT_SOURCE="$_"
if [ -n "$BASH_SOURCE" ]; then
  __SCRIPT_SOURCE="${BASH_SOURCE[0]}"
fi
DIR="$(cd "$(dirname "${__SCRIPT_SOURCE:-$0}")" > /dev/null && \pwd)"
unset __SCRIPT_SOURCE 2> /dev/null

# Load secret credentials
source $DIR/secrets.sh

# Load settings
source $DIR/settings.sh

# Connect to the Carina cluster
eval $(carina env $JUPYTERHUB_CLUSTER)

# Cleanup old containers
docker rm -f nginx jupyterhub letsencrypt &> /dev/null || true

# Build and publish the custom Docker image used by the user's Jupyter server
docker build -t $JUPYTER_IMAGE jupyter
docker push $JUPYTER_IMAGE

# Do all the things with a sidecar of stuff
docker-compose build
docker-compose up -d
docker-compose logs -f
