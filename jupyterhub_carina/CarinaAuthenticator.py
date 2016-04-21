from tornado.auth import OAuth2Mixin
from tornado import gen, web
from traitlets import Dict
from traitlets.config import LoggingConfigurable
from oauthenticator import OAuthLoginHandler, OAuthenticator
from .CarinaOAuthClient import CarinaOAuthClient


class CarinaMixin(OAuth2Mixin):
    _OAUTH_AUTHORIZE_URL = CarinaOAuthClient.CARINA_AUTHORIZE_URL
    _OAUTH_ACCESS_TOKEN_URL = CarinaOAuthClient.CARINA_TOKEN_URL


class CarinaLoginHandler(OAuthLoginHandler, CarinaMixin):
    scope = ['identity', 'cluster_credentials', 'create_cluster']


class CarinaAuthenticator(OAuthenticator, LoggingConfigurable):
    # Configure the base OAuthenticator
    login_service = 'Carina'
    login_handler = CarinaLoginHandler

    # Expose configuration options
    username_map = Dict(config=True, default_value={},
                        help="""Optional dict to remap github usernames to system usernames.

        User github usernames for keys and existing system usernames as values.
        cf https://github.com/jupyter/oauthenticator/issues/28
        """)

    _carina_client = None
    @property
    def carina_client(self):
        if self._carina_client is None:
            self._carina_client = CarinaOAuthClient(self.client_id, self.client_secret, self.oauth_callback_url)

        return self._carina_client

    @gen.coroutine
    def authenticate(self, handler):
        authorization_code = handler.get_argument("code", False)
        if not authorization_code:
            raise web.HTTPError(400, "oauth callback made without a token")

        yield self.carina_client.request_tokens(authorization_code)
        profile = yield self.carina_client.get_user_profile()

        carina_username = profile['username']
        self.carina_client.user = carina_username

        # map username to system username
        system_username = self.username_map.get(carina_username, carina_username)

        # check system username against whitelist
        if self.whitelist and system_username not in self.whitelist:
            system_username = None

        return system_username

    def pre_spawn_start(self, user, spawner):
        """
        Update the spawner with the OAuth credentials from the last time the user signed in
        """
        creds = self.carina_client.credentials
        if creds is None:
            return

        self.log.debug("Updating the spawner with the most recent credentials")
        spawner.carina_client.load_credentials(creds.access_token, creds.refresh_token, creds.expires_at)
