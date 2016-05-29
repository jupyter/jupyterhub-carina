#!/bin/bash

#
# JupyterHub
#

# A space separate list of Carina usernames that should be administrators
# Maps to JupyterHub.Authenticator.admin_users
# Example: myname@example.com arackspaceusername
export JUPYTERHUB_ADMINS=

# The Jupyter server image setup for each user.
# Maps to DockerSpawner.container_image
# Example: dockerhubusername/myworkshop
export JUPYTER_IMAGE=

#
# TLS - If you are not using a domain, leave the variables below blank
#

# The domain of the workshop
# Example: example.com
export JUPYTERHUB_DOMAIN=

# The email address which owns the domain
# Example: myname@example.com
# Used in letsencrypt/reissue.sh
export LETSENCRYPT_EMAIL=

#
# Random - These are all optional settings with which you can customize your Whale in a Box
#

# The carina cluster name where jupyterhub should be deployed. Do not use jupyterhub, or else you will cross the streams!
# Used in setup.sh
export JUPYTERHUB_CLUSTER=whale-in-a-box

# Specifies if production/trusted or staging/untrusted certificate should be generated.
# Staging certs don't count against your rate limit and should be used when first testing this out.
# Used in letsencrypt/reissue.sh
export LETSENCRYPT_USE_PRODUCTION=true
