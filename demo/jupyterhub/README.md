1. Run the following command to create a data volume container to store
    your certificates:

    ```bash
    docker run \
      --name letsencrypt-data \
      --volume /etc/letsencrypt \
      --volume /var/lib/letsencrypt \
      --entrypoint /bin/mkdir \
      quay.io/letsencrypt/letsencrypt \
      -p /etc/letsencrypt/webrootauth/
    ```
1. Run the following command to generate certificates:

    ```bash
    docker run \
      --rm \
      --volumes-from letsencrypt-data \
      --publish 443:443 \
      --publish 80:80 \
      quay.io/letsencrypt/letsencrypt certonly \
      --server https://acme-v01.api.letsencrypt.org/directory \
      --domain dev.howtowhale.com \
      --authenticator standalone \
      --email me@carolynvanslyck.com \
      --agree-tos
    ```

docker run -it --name test \
  -p 8000:8000 \
  -e GITHUB_CLIENT_ID= \
  -e GITHUB_CLIENT_SECRET= \
  -e OAUTH_CALLBACK_URL=http://jupyterhub.carolynvs.com/hub/oauth_callback \
  carolynvs/jupyterhub-carina
