# jupyterhub-carina
Carina support for JupyterHub. Authenticate your users with Carina, then run their Jupyter servers on their own Carina clusters.

For an example of what this looks like, head over to [howtowhale.com](https://howtowhale.com) and sign in with your Carina account.

# Installation
`pip install jupyterhub-carina`

# Prerequisites
JupyterHub communicates with Carina using OAuth. Before your JupyterHub installation can integrate with Carina, you must
first register the application. See the [Carina OAuth documentation][carina-oauth] for instructions on how to register. When asked for the **Redirect URI**, use the following format `https://<jupyterhub_domain>/jupyter/hub/oauth_callback`. The registered callback or redirect URL must match the value in your JupyterHub configuration file.

After you have registered, note the **Application Id**, **Secret** and **Callback URL** because they are required
in order to configure your JupyterHub server to use Carina.

# Configuration

1. Set the `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` environment variables, or use the optional configuration values in the next section to specify your OAuth credentials.
2. Update your [JupyterHub's configuration file][jupyterhub-config], **jupyterhub_config.py**, with the required configuration settings. Replace the placeholder values (denoted with angle brackets) with appropriate values.
    * `<carina_username>`: The username or email address that you use to log into [http://getcarina.com][carina].
    * `<jupyterhub_domain>`: The domain name or IP address of your JupyterHub server.

Below is an example configuration file with only the required values specified:

```python
c = get_config()

# Required: Configure JupyterHub to authenticate against Carina
c.JupyterHub.authenticator_class = "jupyterhub_carina.CarinaAuthenticator"
c.CarinaAuthenticator.admin_users = ["<carina_username>"]
c.CarinaAuthenticator.oauth_callback_url = "https://<jupyterhub_domain>/jupyter/hub/oauth_callback"

# Required: Configure JupyterHub to spawn user servers on Carina
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.spawner_class = "jupyterhub_carina.CarinaSpawner"
c.CarinaSpawner.hub_ip_connect = "<jupyterhub_domain>"
c.CarinaSpawner.oauth_callback_url = "https://<jupyterhub_domain>/jupyter/hub/oauth_callback"
```

## Optional Variables
You can customize how the user's Jupyter server is created or how your OAuth credentials are specified.

* `<cluster_name>`: The name of the Carina cluster to create for users. Defaults to `jupyterhub`.
* `<container_prefix>`: The prefix for the container running the user's server. Defaults to `jupyter`, resulting in a
    container named `jupyter-<username>`.
* `<container_image>`: The name of the image to use for the user's server. Defaults to `jupyter/singleuser`.
* `<cluster_polling_interval>`: The number of seconds between polling for a user's Carina cluster to become active.
    Defaults to `30` seconds.
* `<client_id_env>`: The environment variable containing your Carina OAuth Application Id.
    Defaults to `OAUTH_CLIENT_ID`.
* `<client_secret_env>`: The environment variable containing your Carina OAuth Secret.
    Defaults to `OAUTH_CLIENT_SECRET`.
* `<client_id>`: Your Carina OAuth Application Id. Defaults to the value found in the `<client_id_env>` environment variable.
    For example, you may load this from a config file. _Do NOT hard code this values and check it in!_
* `<client_secret>`: Your Carina OAuth Secret. Defaults to the value found in the `<client_secret_env>` environment variable.
    For example, you may load this from a config file. _Do NOT hard code this values and check it in!_

Below is an example configuration file with all required and optional values specified:

```python
c = get_config()

# Required: Configure JupyterHub to authenticate against Carina
c.JupyterHub.authenticator_class = "jupyterhub_carina.CarinaAuthenticator"
c.CarinaAuthenticator.admin_users = ["<carina_username>"]
c.CarinaAuthenticator.oauth_callback_url = "https://<jupyterhub_domain>/jupyter/hub/oauth_callback"

# Required: Configure JupyterHub to spawn user servers on Carina
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.spawner_class = "jupyterhub_carina.CarinaSpawner"
c.CarinaSpawner.hub_ip_connect = "<jupyterhub_domain>"
c.CarinaSpawner.oauth_callback_url = "https://<jupyterhub_domain>/jupyter/hub/oauth_callback"

# Optional: Tweak how the CarinaSpawner creates the user's Carina cluster and container
c.CarinaSpawner.cluster_name = "<cluster_name>"
c.CarinaSpawner.container_prefix = "<container_prefix>"
c.CarinaSpawner.container_image = "<container_image>"
c.CarinaSpawner.cluster_polling_interval = "<cluster_polling_interval>"

# Optional: Tweak where your Carina OAuth application's credentials are located
c.CarinaAuthenticator.client_id_env = "<client_id_env>"
c.CarinaSpawner.client_id_env = "<client_id_env>"
c.CarinaAuthenticator.client_secret_env = "<client_secret_env>"
c.CarinaSpawner.client_secret_env = "<client_secret_env>"

# Optional: Directly specify your Carina OAuth application's credentials
c.CarinaAuthenticator.client_id = "<client_id>"
c.CarinaSpawner.client_id = "<client_id>"
c.CarinaAuthenticator.client_secret = "<client_secret>"
c.CarinaSpawner.client_secret = "<client_secret>"
```

[carina]: http://getcarina.com
[carina-oauth]: https://getcarina.com/docs/reference/oauth-integration/#register-your-application
[jupyterhub-config]: http://jupyterhub.readthedocs.org/en/latest/getting-started.html#how-to-configure-jupyterhub