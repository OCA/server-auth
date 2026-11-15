# Copyright 2026 ThinkTop
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
"""PKCE ``code_verifier`` handling, kept out of the database.

RFC 7636 section 5.1 asks for a fresh, unpredictable ``code_verifier`` for
every authorization request. Keeping it on the provider record means one
value is shared by every user for the whole lifetime of the provider, and
that it sits in a table anyone with read access can query. A captured
authorization code can then be exchanged -- which is precisely what PKCE
exists to prevent.

The session is the natural place for it: per-user, per-browser, and carried
across the redirect round-trip by the session cookie. One browser can start
several authorizations at once, though -- several tabs, or the login page
rendered again while one is still in flight -- so each verifier is filed
under a random key that is also carried in the OAuth ``state`` parameter.
The callback then claims exactly the verifier belonging to it, and two
concurrent authorizations do not invalidate each other.

Nothing is stored in the database, migrated, or cleaned up by a cron: an
entry is dropped as soon as it is claimed, and the session expires.
"""

import secrets

SESSION_KEY = "auth_oidc_code_verifiers"
REQUEST_ATTR = "auth_oidc_code_verifiers"
STATE_KEY = "k"
# A few concurrent authorizations is plenty; the oldest entries are dropped
# so that a session cannot grow without bound.
MAX_PENDING = 8


def _session():
    """Return the current session, or ``None`` outside a request."""
    try:
        from odoo.http import request

        return getattr(request, "session", None)
    except RuntimeError:  # request not bound (CLI, cron)
        return None


def issue():
    """Generate a fresh verifier."""
    return secrets.token_urlsafe(32)


def current_verifier(provider_id):
    """Return the verifier issued for ``provider_id`` during this request.

    Verifiers are generated here rather than on the provider record, and
    cached on the request so that a page listing providers more than once
    yields the same value -- otherwise the challenge rendered into the link
    and the one filed in the session could drift apart.
    """
    from odoo.http import request

    try:
        verifiers = getattr(request, REQUEST_ATTR, None)
        if not isinstance(verifiers, dict):
            verifiers = {}
            setattr(request, REQUEST_ATTR, verifiers)
    except (RuntimeError, AttributeError, TypeError):
        # request not bound (CLI, cron), or a request object that does not
        # take attributes; a fresh value per call is still correct
        return issue()
    return verifiers.setdefault(provider_id, issue())


def remember(verifier, state):
    """File ``verifier`` in the session and tag ``state`` with its key.

    ``state`` is the dict later JSON-encoded into the OAuth ``state``
    parameter. It is updated in place and returned.
    """
    session = _session()
    if session is None:
        return state
    pending = dict(session.get(SESSION_KEY) or {})
    key = next((k for k, v in pending.items() if v == verifier), None)
    if key is None:
        key = secrets.token_urlsafe(16)
        pending[key] = verifier
        while len(pending) > MAX_PENDING:
            pending.pop(next(iter(pending)))
        session[SESSION_KEY] = pending
    state[STATE_KEY] = key
    return state


def claim(state):
    """Return and forget the verifier filed for ``state``.

    Returns an empty string when there is none: an authorization started
    before the upgrade, or a callback that did not come through
    ``list_providers()``. The token request then fails at the provider,
    which is a controlled failure, rather than raising here.
    """
    session = _session()
    key = state.get(STATE_KEY) if isinstance(state, dict) else None
    if not key or session is None:
        return ""
    pending = dict(session.get(SESSION_KEY) or {})
    verifier = pending.pop(key, "")
    session[SESSION_KEY] = pending
    return verifier
