from tornado.auth import OAuth2Mixin
from tornado import gen, web
from traitlets.config import LoggingConfigurable
from oauthenticator import OAuthLoginHandler, OAuthenticator
from .CarinaOAuthClient import CarinaOAuthClient


class CarinaLoginHandler(OAuthLoginHandler, OAuth2Mixin):
    """
    Carina OAuth dance magic
    """

    _OAUTH_AUTHORIZE_URL = CarinaOAuthClient.CARINA_AUTHORIZE_URL
    _OAUTH_ACCESS_TOKEN_URL = CarinaOAuthClient.CARINA_TOKEN_URL

    scope = ['identity', 'read', 'write', 'execute']


class CarinaAuthenticator(OAuthenticator, LoggingConfigurable):
    """
    Authenticate users with their Carina account
    """

    # Configure the base OAuthenticator
    login_service = 'Carina'
    login_handler = CarinaLoginHandler

    _carina_client = None
    @property
    def carina_client(self):
        if self._carina_client is None:
            self._carina_client = CarinaOAuthClient(self.client_id, self.client_secret, self.oauth_callback_url)

        return self._carina_client

    @gen.coroutine
    def authenticate(self, handler, data=None):
        """
        Complete the OAuth dance and identify the user
        """
        authorization_code = handler.get_argument("code", False)
        if not authorization_code:
            raise web.HTTPError(400, "OAuth callback made without a token")

        yield self.carina_client.request_tokens(authorization_code)
        profile = yield self.carina_client.get_user_profile()

        carina_username = profile['username']
        self.carina_client.user = carina_username

        # verify that the user is authorized on this system
        if self.whitelist and carina_username not in self.whitelist:
            carina_username = None

        return carina_username

    def pre_spawn_start(self, user, spawner):
        """
        Update the spawner with the most recent OAuth credentials
        """
        creds = self.carina_client.credentials
        if creds is None:
            return

        self.log.debug("Updating the spawner with the most recent credentials")
        spawner.carina_client.load_credentials(creds.access_token, creds.refresh_token, creds.expires_at)
