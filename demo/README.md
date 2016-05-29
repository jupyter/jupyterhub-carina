# Whale in a Box
Want to run a workshop or class? Don't want to waste time setting up and troubleshooting
everyone's snowflake laptops?

This will get you setup with your own JupyterHub instance, running on Carina.
Each participant can log in with their Carina account to have their own pre-setup sandbox,
with any Jupyter notebooks and materials included.

# Prerequisites
* A Carina account. If you do not already have one, create a free account (no credit card required)
  by following the [sign up process](https://app.getcarina.com/app/signup).
* Your Carina API key. To get it, go to the [Carina Control Panel](https://app.getcarina.com),
  click your username in the top-right corner, and then click API Key.

# Installation
1. Download or clone this repository.
1. Open a terminal in the `demo` subdirectory.
1. Create a file to contain secret credentials. Do **not** check-in this file.

    **Bash**

    Name the file `secrets.sh` and add the following content:

    ```bash
    export CARINA_USERNAME=username
    export CARINA_APIKEY=apikey
    ```

    **PowerShell**

    Name the file `secrets.ps1` and add the following content:

    ```powershell
    $env:CARINA_USERNAME="username"
    $env:CARINA_APIKEY="apikey"
    ```  
1. Run the following command to perform one-time setup for the workshop infrastructure:

    **Bash**

    ```bash
    $ ./setup.sh

    ```

    **PowerShell**

    ```powershell
    > .\setup.sh
    ```
1. The output contains the IP address of the workshop website. If you have a
    domain for the workshop, update your DNS and add an A record pointing to the IP address.
    Depending on TTL settings, this will a few minutes or longer.

    You can determine when the entry is ready by running the following command,
    replacing `<myDomain>` with your domain name:

    **Bash**

    ```bash
    $ dig +short <myDomain>
    172.99.73.144
    ```

    **PowerShell**

    ```powershell
    > nslookup <myDomain>
    Server:  FIOS_Quantum_Gateway.fios-router.home
    Address:  192.168.1.1

    Non-authoritative answer:
    Name:    <myDomain>
    Address:  172.99.73.144
    ```

1. Go to your domain, or the IP address and verify that the website works.
1. [Register the website with Carina OAuth](https://getcarina.com/docs/reference/oauth-integration/#register-your-application).
    For the **Callback URL** use `https://<domain-or-ip>/jupyter/hub/oauth_callback`.
1. Add your Carina OAuth credentials to the secrets file.

    **Bash**

    Edit `secrets.sh` and add the following content:

    ```bash
    export CARINA_OAUTH_CLIENT_ID=application-id
    export CARINA_OAUTH_CLIENT_SECRET=secret
    ```

    **PowerShell**

    Edit `secrets.ps1` and add the following content:

    ```poweshell
    $env:CARINA_OAUTH_CLIENT_ID="application-id"
    $env:CARINA_OAUTH_CLIENT_SECRET="secret"
    ```
1. Customize the settings file following the directions in the file.
    If you are using PowerShell, edit `settings.ps1`, otherwise `settings.sh`.
1. Run the following command to create the workshop website. This command can be
    rerun at any time to update the website assets, workshop materials, or just fix things
    if they break.

    **Bash**

    ```bash
    $ ./run.sh
    ```

    **PowerShell**

    ```powershell
    > .\run.sh
    ```

# Customization
This is a mighty fine boxed whale, ready to be taken home and turned into your very
own howtowhale. Most things are tweakable without having to delve into the deployment
infrastructure.

## Materials
Add Jupyter notebooks and other materials to `jupyter/materials` and redeploy.

## Landing Page
Edit `web/index.html` and redeploy.

## Jupyter Server
Edit `jupyter/Dockerfile` to either swap out the base Jupyter notebook server image
or add dependencies.

* Change `FROM jupyter/minimal-notebook` to another
base Jupyter notebook server of your choice. I recommend selecting one from the
[Jupyter Docker Stacks project](https://github.com/jupyter/docker-stacks#a-visual-overview-of-stacks).
* Add `RUN <command>` to install additional dependencies, for example `RUN apt-get update && apt-get install -y curl` or `RUN pip install pandas`.
