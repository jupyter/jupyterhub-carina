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

echo "Performing one-time setup"

# Install carina
if ! type carina > /dev/null; then
  echo "Installing the carina cli"
  curl -L https://download.getcarina.com/carina/latest/$(uname -s)/$(uname -m)/carina > /usr/local/bin/carina
  chmod +x /usr/local/bin/carina
fi

# Install dvm
if ! type dvm > /dev/null; then
  echo "Installing dvm"
  curl -sL https://download.getcarina.com/dvm/latest/install.sh | sh
  source ~/.dvm/dvm.sh
fi

# Install docker-compose
if ! type docker-compose > /dev/null; then
  echo "Installing docker-compose"
  curl -L https://github.com/docker/compose/releases/download/1.7.1/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
fi

# Create a cluster on Carina
if ! carina get $JUPYTERHUB_CLUSTER 2>&1 | grep -q $JUPYTERHUB_CLUSTER &> /dev/null; then
  echo "Creating a Carina cluster..."
  carina create --wait $JUPYTERHUB_CLUSTER
fi
eval $(carina env $JUPYTERHUB_CLUSTER)

# Use the right docker client for the cluster
dvm use &> /dev/null

# Login to Docker Hub
docker login

# Print out the IP address of the cluster
# TODO: Since we have their api key already, check if they have a Rackspace DNS entry for this domain
# If so, prompt to add/update the A record on their behalf, and then wait for the DNS change to propogate
printf "\n##########\n"
echo "All done!"
echo "If you are running JupyterHub with a domain name, add an A record to your DNS now pointing to the IP address below:"
printf "##########\n"
docker run --rm --net=host -e constraint:node==*-n1 racknet/ip public ipv4
