import docker
from dockerspawner import DockerSpawner
import os.path
import re
import shutil
from tornado import gen
from traitlets import Dict, Integer, Unicode
from .CarinaOAuthClient import CarinaOAuthClient


class CarinaSpawner(DockerSpawner):
    """
    Spawn the user's Jupyter server on their Carina cluster
    """

    cluster_name = Unicode(
        'jupyterhub',
        help="The name of the user's Carina cluster.",
        config=True)

    # Override the default container name. Since we are running on the user's cluster, we don't
    # need the username suffix
    container_name = Unicode(
        'jupyter',
        help="The name of the Jupyter server container running on the user's cluster.",
        config=True)

    cluster_polling_interval = Integer(
        30,
        help="The number of seconds between polling for a user's cluster to become active.",
        config=True
    )

    # Override the default timeout to allow extra time for creating the cluster and pulling the
    # server image
    start_timeout = Integer(
        300,
        help=DockerSpawner.start_timeout.help,
        config=True)

    # Override the docker run parameters
    extra_host_config = Dict(
        {
            'volumes_from': ['swarm-data'],  # --volumes-from swarm-data
            'port_bindings': {8888: None},  # -p 8888:8888
            'restart_policy': {  # --restart always
                'MaximumRetryCount': 0,
                'Name': 'always'
            },
        },
        help=DockerSpawner.extra_host_config.help,
        config=True)

    def __init__(self, **kwargs):
        # Use a different docker client for each server
        self._client = None
        self._carina_client = None

        super().__init__(**kwargs)

    @property
    def client(self):
        """
        The Docker client used to connect to the user's Carina cluster
        """
        # TODO: Figure out how to configure this without overriding, or tweak a bit and call super
        if self._client is None:
            carina_dir = self.get_user_credentials_dir()
            docker_env = os.path.join(carina_dir, 'docker.env')
            if not os.path.exists(docker_env):
                raise RuntimeError(
                    "ERROR! The credentials for {}/{} could not be found in {}.".format(
                        self.user.name, self.cluster_name, carina_dir))

            tls_config = docker.tls.TLSConfig(
                client_cert=(os.path.join(carina_dir, 'cert.pem'),
                             os.path.join(carina_dir, 'key.pem')),
                ca_cert=os.path.join(carina_dir, 'ca.pem'),
                verify=os.path.join(carina_dir, 'ca.pem'),
                assert_hostname=False)
            with open(docker_env) as f:
                env = f.read()
            docker_host = re.findall("DOCKER_HOST=tcp://(\d+\.\d+\.\d+\.\d+:\d+)", env)[0]
            docker_host = 'https://' + docker_host
            self._client = docker.Client(version='auto', tls=tls_config, base_url=docker_host)

        return self._client

    @property
    def carina_client(self):
        if self._carina_client is None:
            self.log.debug("Initializing a carina client for %s", self.user.name)
            # Load OAuth configuration from the authenticator
            cfg = self.authenticator
            self._carina_client = CarinaOAuthClient(cfg.client_id, cfg.client_secret,
                                                    cfg.oauth_callback_url,
                                                    user=self.user.name)

        return self._carina_client

    def get_state(self):
        self.log.debug("Saving state for %s", self.user.name)
        state = super().get_state()
        if self.carina_client.credentials:
            state['access_token'] = self.carina_client.credentials.access_token
            state['refresh_token'] = self.carina_client.credentials.refresh_token
            state['expires_at'] = self.carina_client.credentials.expires_at

        return state

    def load_state(self, state):
        self.log.debug("Loading state for %s", self.user.name)
        super().load_state(state)

        access_token = state.get('access_token', None)
        refresh_token = state.get('refresh_token', None)
        expires_at = state.get('expires_at', None)
        if access_token:
            self.log.debug("Loading users's oauth credentials")
            self.carina_client.load_credentials(access_token, refresh_token, expires_at)

    def clear_state(self):
        self.log.debug("Clearing state")
        super().clear_state()

        # TODO: Move this to DockerSpawner
        self.container_id = ''

    @gen.coroutine
    def get_container(self):
        if not (yield self.cluster_exists()):
            return None

        container = yield super().get_container()
        return container

    def get_env(self):
        env = super().get_env()

        self.log.debug("Adding Docker environment variables to the Jupyter server")
        env['DOCKER_HOST'] = self.client.base_url.replace("https://", "tcp://")
        env['DOCKER_TLS_VERIFY'] = 1
        env['DOCKER_CERT_PATH'] = '/var/run/docker/'

        return env

    @gen.coroutine
    def start(self):
        try:
            self.log.info("Creating infrastructure for {}...".format(self.user.name))
            cluster = yield self.create_cluster()
            yield self.download_cluster_credentials(cluster['id'])
            yield self.pull_user_image()

            self.log.info("Starting container for {}...".format(self.user.name))
            yield super().start()

            self.log.debug('Startup for {} is complete!'.format(self.user.name))
        except Exception:
            self.log.exception('Startup for {} failed!'.format(self.user.name))
            raise

    @gen.coroutine
    def create_cluster(self):
        """
        Create a Carina cluster
        """
        self.log.info("Creating cluster named: {} for {}".format(self.cluster_name, self.user.name))
        return (yield self.carina_client.create_cluster(self.cluster_name))

    @gen.coroutine
    def download_cluster_credentials(self, cluster_id):
        """
        Download the cluster credentials
        """
        credentials_dir = self.get_user_credentials_dir()
        if os.path.exists(credentials_dir):
            return

        self.log.info("Downloading cluster credentials for {}/{} ({})..."
                      .format(self.user.name, self.cluster_name, cluster_id))
        user_dir = "/root/.carina/clusters/{}".format(self.user.name)
        yield self.carina_client.download_cluster_credentials(cluster_id, self.cluster_name,
                                                              user_dir,
                                                              self.cluster_polling_interval)

    @gen.coroutine
    def cluster_exists(self):
        """
        Safely check if the user's cluster exists
        """
        credentials_dir = self.get_user_credentials_dir()
        if not os.path.exists(credentials_dir):
            return False

        try:
            yield self.docker('info')
            return True
        except Exception:
            # Remove old credentials now that they no longer work
            shutil.rmtree(credentials_dir, ignore_errors=True)
            self._client = None
            return False

    @gen.coroutine
    def pull_user_image(self):
        """
        Pull the user image to the cluster
        """
        self.log.debug("Starting to pull {} to the {}/{} cluster..."
                       .format(self.container_image, self.user.name, self.cluster_name))
        yield self.docker("pull", self.container_image)
        self.log.debug("Finished pulling {} to the {}/{} cluster..."
                       .format(self.container_image, self.user.name, self.cluster_name))

    def get_user_credentials_dir(self):
        credentials_dir = "/root/.carina/clusters/{}/{}".format(self.user.name, self.cluster_name)
        return credentials_dir
