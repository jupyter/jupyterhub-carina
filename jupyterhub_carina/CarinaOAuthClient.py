import json
import os
from time import time, ctime
from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPError, AsyncHTTPClient
from traitlets.config import LoggingConfigurable
import urllib
from zipfile import ZipFile
from ._version import __version__

class CarinaOAuthCredentials:
    """
    A set of Carina OAuth credentials
    """

    def __init__(self, access_token, refresh_token, expires_at):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at

    def is_expired(self):
        """
        Check if the access_token is, or is about to be, expired
        """
        return time() >= (self.expires_at + 60)


class CarinaOAuthClient(LoggingConfigurable):
    """
    Communicates with Carina via the OAuth2 protocol
    """

    CARINA_OAUTH_HOST = os.environ.get('CARINA_OAUTH_HOST') or 'oauth.getcarina.com'
    CARINA_AUTHORIZE_URL = "https://%s/oauth/authorize" % CARINA_OAUTH_HOST
    CARINA_TOKEN_URL = "https://%s/oauth/token" % CARINA_OAUTH_HOST
    CARINA_PROFILE_URL = "https://%s/users/current" % CARINA_OAUTH_HOST
    CARINA_CLUSTERS_URL = "https://%s/proxy/clusters" % CARINA_OAUTH_HOST
    CARINA_TEMPLATES_URL = "https://%s/proxy/cluster_types" % CARINA_OAUTH_HOST

    def __init__(self, client_id, client_secret, callback_url, user='UNKNOWN'):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = callback_url
        self.credentials = None
        self.user = user

    def load_credentials(self, access_token, refresh_token, expires_at):
        self.credentials = CarinaOAuthCredentials(access_token, refresh_token, expires_at)

    @gen.coroutine
    def request_tokens(self, authorization_code):
        """
        Exchange an authorization code for access and refresh tokens

        See: https://github.com/doorkeeper-gem/doorkeeper/wiki/API-endpoint-descriptions-and-examples#post---oauthtoken
        """
        self.log.debug("Requesting oauth tokens")
        body = {
            'code': authorization_code,
            'grant_type': 'authorization_code'
        }

        yield self.execute_token_request(body)

    @gen.coroutine
    def refresh_tokens(self):
        """
        Exchange a refresh token for a new set of tokens

        See: https://github.com/doorkeeper-gem/doorkeeper/wiki/API-endpoint-descriptions-and-examples#curl-command-refresh-token-grant
        """
        self.log.info("Refreshing oauth tokens for %s", self.user)
        body = {
            'refresh_token': self.credentials.refresh_token,
            'grant_type': 'refresh_token'
        }

        yield self.execute_token_request(body)

    @gen.coroutine
    def get_user_profile(self):
        """
        Determine the identity of the current user
        """
        self.log.debug("Retrieving the user profile")
        request = HTTPRequest(
            url=self.CARINA_PROFILE_URL,
            method='GET',
            headers={
                'Accept': 'application/json',
            })
        response = yield self.execute_oauth_request(request)
        result = json.loads(response.body.decode('utf8', 'replace'))
        return result

    @gen.coroutine
    def create_cluster(self, cluster_name):
        """
        Create a Carina cluster
        """
        template_id = yield self.lookup_swarm_template()

        self.log.info("Creating cluster %s/%s using template %d", self.user, cluster_name,
                      template_id)
        request = HTTPRequest(
            url=self.CARINA_CLUSTERS_URL,
            method='POST',
            body=json.dumps({
                      "cluster_type_id": template_id,
                      "node_count": 1,
                      "name": cluster_name
                      }),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        self.log.info("Request: %s", request.body)

        response = yield self.execute_oauth_request(request)
        result = json.loads(response.body.decode('utf8', 'replace'))
        self.log.info("Response: %s", response.body)

        return result

    @gen.coroutine
    def lookup_swarm_template(self):
        """
        Lookup the latest template for Docker Swarm
        """
        self.log.info("Looking up latest Carina swarm template")
        request = HTTPRequest(
            url=self.CARINA_TEMPLATES_URL,
            method='GET',
            headers={
                'Accept': 'application/json'
            })

        response = yield self.execute_oauth_request(request)
        results = json.loads(response.body.decode('utf8', 'replace'))

        # Get the most recent template for Docker Swarm
        template_id = 0
        for result in results['cluster_types']:
            if result['coe'] == 'swarm' and result['id'] > template_id:
                template_id = result['id']

        if template_id == 0:
            raise Exception('Unable to find a Docker Swarm template')

        return template_id

    @gen.coroutine
    def download_cluster_credentials(self, cluster_id, cluster_name, destination,
                                     polling_interval=30):
        """
        Download a cluster's credentials to the specified location

        The API will return 404 if the cluster isn't available yet,
        in which case the request should be retried.
        """
        self.log.info("Downloading cluster credentials for %s/%s (%s)",
                      self.user, cluster_name, cluster_id)
        request = HTTPRequest(
            url=os.path.join(self.CARINA_CLUSTERS_URL, cluster_id, 'credentials/zip'),
            method='GET',
            headers={
                'Accept': 'application/zip'
            })

        # Poll for the cluster credentials until the cluster is active
        while True:
            response = yield self.execute_oauth_request(request, raise_error=False)

            if response.error is None:
                self.log.debug("Credentials for %s/%s (%s) received.",
                               self.user, cluster_name, cluster_id)
                break

            if response.code == 404 and "Cluster credentials do not exist" in response.body.decode(
                    encoding='UTF-8'):
                self.log.debug("The %s/%s (%s) cluster is not yet active, retrying in %s "
                               "seconds...", self.user, cluster_name, cluster_id, polling_interval)
                yield gen.sleep(polling_interval)
                continue

            # abort, something bad happened!
            self.log.error(
                'An error occurred while downloading cluster credentials for %s/%s (%s):\n'
                '(%s) %s\n%s',
                self.user, cluster_name, cluster_id,
                response.code, response.body, response.error)
            response.rethrow

        credentials_zip = ZipFile(response.buffer, "r")
        credentials_zip.extractall(destination)
        self.log.info("Credentials downloaded to %s", destination)

    @gen.coroutine
    def execute_token_request(self, body):
        """
        Requests a new set of OAuth tokens
        """
        body.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.callback_url
        })

        request = HTTPRequest(
            url=self.CARINA_TOKEN_URL,
            method='POST',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body=urllib.parse.urlencode(body)
        )

        request_timestamp = time()
        response = yield self.execute_request(request)

        result = json.loads(response.body.decode('utf8', 'replace'))
        self.credentials = CarinaOAuthCredentials(
            access_token=result['access_token'],
            refresh_token=result['refresh_token'],
            expires_at=request_timestamp + int(result['expires_in']))

    @gen.coroutine
    def execute_oauth_request(self, request, raise_error=True):
        """
        Execute an OAuth request

        Retry with a new set of tokens when the OAuth access token is expired or rejected
        """
        if self.credentials.is_expired():
            self.log.info("The OAuth token for %s expired at %s", self.user,
                          ctime(self.credentials.expires_at))
            yield self.refresh_tokens()

        self.authorize_request(request)

        try:
            return (yield self.execute_request(request, raise_error))
        except HTTPError as e:
            if e.response.code != 401:
                raise

            # Try once more with a new set of tokens
            self.log.info("The OAuth token for %s was rejected", self.user)
            yield self.refresh_tokens()
            self.authorize_request(request)
            return (yield self.execute_request(request, raise_error))

    def authorize_request(self, request):
        """
        Add the Authorization header with the user's OAuth access token to a request
        """
        request.headers.update({
            'Authorization': 'bearer {}'.format(self.credentials.access_token)
        })

    @gen.coroutine
    def execute_request(self, request, raise_error=True):
        """
        Execute an HTTP request and log the error, if any
        """

        self.log.debug("%s %s", request.method, request.url)
        http_client = AsyncHTTPClient()
        request.headers.update({
            'User-Agent': 'jupyterhub-carina/' + __version__
        })
        try:
            return (yield http_client.fetch(request, raise_error=raise_error))
        except HTTPError as e:
            self.log.exception('An error occurred executing %s %s:\n(%s) %s',
                               request.method, request.url, e.response.code, e.response.body)
            raise
