# Copyright 2026 Nimarosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)

# Spellings of the "this e-mail was verified by the provider" claim.
# ``email_verified`` is the OpenID Connect standard one (Google's
# /oauth2/v3/userinfo); ``verified_email`` is the legacy Google tokeninfo v1
# spelling, still returned by some deployments.
VERIFIED_EMAIL_CLAIMS = ("email_verified", "verified_email")
TRUTHY_CLAIM_VALUES = ("true", "1", "yes")


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """Link the verified identity to an existing user before sign-in.

        Stock ``auth_oauth`` recognises a user only by the ``oauth_uid`` stored
        on it, so a user created by an administrator can never log in through
        OAuth: the lookup misses, the flow falls through to signup, and a B2B
        database refuses it. This override performs that first link once, and
        only under the conditions in :meth:`_auth_oauth_autolink_find_user`.

        The link is deliberately made **here**, right after the provider
        vouched for the identity, and not in ``_auth_oauth_signin``:

        * By the time the sign-in chain runs, the user is already linked, so
          every other module overriding ``_auth_oauth_signin`` sees an ordinary
          already-linked user. ``auth_oauth_multi_token`` in particular reads
          its recordset *before* delegating to ``super()`` and raises
          ``AccessDenied`` on it afterwards, which no amount of cooperation
          from inside that chain could satisfy.
        * The access token stays the business of the stock implementation (and
          of ``auth_oauth_multi_token`` when installed), so this module never
          has to guess how a token should be stored.

        Doing it before sign-in is also what keeps a signup-enabled (B2C)
        database safe: ``super()`` would otherwise try to *create* a user with
        the very login about to be linked, which fails on the ``login`` unique
        index and poisons the transaction.
        """
        validation = super()._auth_oauth_validate(provider, access_token)
        self._auth_oauth_autolink(provider, validation)
        return validation

    @api.model
    def _auth_oauth_autolink(self, provider, validation):
        """Link this OAuth identity to an existing user, once.

        Returns the linked user, or an empty recordset when nothing was
        linked -- which is the normal outcome for every login after the first
        one, and for every request that does not pass all the guards.
        """
        oauth_uid = validation["user_id"]
        already_linked = self.sudo().search_count(
            [("oauth_uid", "=", oauth_uid), ("oauth_provider_id", "=", provider)],
        )
        if already_linked:
            # An ordinary login: the stock flow resolves it on its own.
            return self.browse()
        user = self._auth_oauth_autolink_find_user(provider, validation)
        if not user:
            return self.browse()
        user.write({"oauth_provider_id": provider, "oauth_uid": oauth_uid})
        self._auth_oauth_autolink_log(user)
        return user

    @api.model
    def _auth_oauth_autolink_find_user(self, provider, validation):
        """Return the single user this OAuth account may be linked to, or None.

        Every guard here is deliberate; a ``None`` return means the caller
        leaves the stock flow alone, which raises the usual ``AccessDenied``
        without disclosing which guard refused.
        """
        oauth_provider = self.env["auth.oauth.provider"].sudo().browse(provider)
        if not oauth_provider.autolink_by_email:
            return None
        if not self._auth_oauth_autolink_is_email_verified(validation):
            _logger.info(
                "OAuth auto-link refused for provider %s: the provider did not "
                "report the e-mail address as verified.",
                oauth_provider.name,
            )
            return None
        email = email_normalize(validation.get("email"))
        if not email:
            return None
        # ``=ilike`` is a pattern match, so a login containing '%' or '_' can
        # widen the candidate set; the normalized comparison below is what
        # actually decides. ``search`` excludes archived users by default,
        # which is why an inactive user is never linked.
        candidates = self.sudo().search([("login", "=ilike", email)])
        matches = candidates.filtered(lambda user: email_normalize(user.login) == email)
        if len(matches) != 1:
            if matches:
                # Logged at INFO on purpose: an ambiguous e-mail is a refusal,
                # not a server fault, and this runs on every such login.
                _logger.info(
                    "OAuth auto-link refused: %s active users share the login %s.",
                    len(matches),
                    email,
                )
            return None
        if matches.oauth_uid:
            _logger.info(
                "OAuth auto-link refused: user %s is already linked to an "
                "OAuth account.",
                matches.login,
            )
            return None
        return matches

    @api.model
    def _auth_oauth_autolink_is_email_verified(self, validation):
        """Whether the provider vouches for the ownership of the e-mail.

        An absent claim is treated as *not* verified: it is the whole trust
        anchor of this module, so it is never assumed.
        """
        for claim in VERIFIED_EMAIL_CLAIMS:
            value = validation.get(claim)
            if value is True:
                return True
            if isinstance(value, str) and value.strip().lower() in TRUTHY_CLAIM_VALUES:
                return True
        return False

    def _auth_oauth_autolink_log(self, user):
        provider_name = user.oauth_provider_id.sudo().name
        _logger.info(
            "OAuth auto-link: user %s (id %s) linked to provider %s by verified "
            "e-mail on first OAuth login.",
            user.login,
            user.id,
            provider_name,
        )
        # res.users is not a mail.thread; the chatter lives on its partner.
        user.partner_id.sudo().message_post(
            body=_(
                "Linked to the %(provider)s account by verified e-mail on first "
                "OAuth login.",
                provider=provider_name,
            )
        )
