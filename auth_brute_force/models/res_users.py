import logging
from contextlib import contextmanager

from odoo import api, models, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    # Helper: Track Authentication Attempt
    @classmethod
    @contextmanager
    def _auth_attempt(cls):
        """Track an authentication attempt based on request login."""
        try:
            cls.environ = request.httprequest.environ
        except RuntimeError:
            yield
            return

        # Extract login from request
        login = request.params.get("login")

        attempt_id = cls.environ.get("auth_attempt_id")

        # Create new attempt only if first call
        if not attempt_id:
            attempt_id = cls._auth_attempt_new(login)

        if not attempt_id:
            yield
            return

        cls.environ["auth_attempt_id"] = attempt_id
        result = "successful"

        try:
            yield
        except AccessDenied as error:
            result = getattr(error, "reason", "failed")
            raise
        finally:
            cls._auth_attempt_update({"result": result})
            cls.environ.pop("auth_attempt_id", None)

    @classmethod
    def _auth_attempt_force_raise(cls, method):
        """Force a method to raise an AccessDenied on falsey return."""
        with cls._auth_attempt():
            print('INSIDE')
            return method()

    @classmethod
    def _auth_attempt_new(cls, login):
        """Store one authentication attempt, not knowing the result."""
        # Get the right remote address
        remote_addr = getattr(request.httprequest, "remote_addr", None)
        # Exit if it doesn't make sense to store this attempt
        if not remote_addr:
            return False
        # Use a separate cursor to keep changes always
        reg = Registry(request.db)
        with reg.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            attempt = env["res.authentication.attempt"].create(
                {
                    "login": login,
                    "remote": remote_addr,
                }
            )
            return attempt.id

    @classmethod
    def _auth_attempt_update(cls, values):
        """Update a given auth attempt if we still ignore its result."""
        auth_id = cls.environ.get("auth_attempt_id") if hasattr(cls, "environ") else False
        if not auth_id:
            return {}  # No running auth attempt; nothing to do
        # Use a separate cursor to keep changes always
        with cls.pool.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            attempt = env["res.authentication.attempt"].browse(auth_id)
            # Update only on 1st call
            if attempt.exists() and not attempt.result:
                attempt.write(values)
            return attempt.copy_data()[0] if attempt else {}

    # Override all auth-related core methods
    @classmethod
    def _login(cls, db, password, user_agent_env):
        return cls._auth_attempt_force_raise(
            lambda: super(ResUsers, cls)._login(
                db, password, user_agent_env
            )
        )

    @classmethod
    def authenticate(cls, db, password, user_agent_env):
        print('\n\n User db----------',db)
        print('\n\n User password----------',password)
        print('\n\n User user_agent_env----------',user_agent_env)
        res = cls._auth_attempt_force_raise(
            lambda: super(ResUsers, cls).authenticate(
                db, password, user_agent_env
            )
        )
        print('\n\n User res----------', res)
        return res

    @api.model
    def _check_credentials(self, credential, env):
        """This is the most important and specific auth check method.
        When we get here, it means that Odoo already checked the user exists
        in this database.
        Other auth methods usually plug here.
        """
        with self._auth_attempt():
            login = self.env.user.login
            # Update login, just in case we stored the UID before
            attempt = self._auth_attempt_update({"login": login})
            remote = attempt.get("remote")
            # Fail if the remote is banned
            trusted = self.env["res.authentication.attempt"]._trusted(remote, login)
            if not trusted:
                raise AccessDenied("banned")
            # Continue with other auth systems
            return super(ResUsers, self)._check_credentials(credential, env)
