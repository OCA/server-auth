# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Stateless helpers of the authorization server.

The two functions that reach the network, ``resolve_host`` and
``fetch_metadata_document``, are module-level so that tests can patch them.
Call them as ``utils.resolve_host(...)``, never import them by name.
"""

import base64
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import socket
import time
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import requests

from odoo.tools import consteq

TOKEN_BYTES = 32
MAX_URI_LENGTH = 2048
PKCE_VERIFIER_RE = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")
# base64url without padding of a SHA-256 digest
PKCE_CHALLENGE_RE = re.compile(r"^[A-Za-z0-9\-_]{43}$")
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
METADATA_DOCUMENT_MAX_BYTES = 5 * 1024
METADATA_DOCUMENT_TIMEOUT = 5
NAT64_NETWORK = ipaddress.ip_network("64:ff9b::/96")


def generate_token(nbytes=TOKEN_BYTES):
    return secrets.token_urlsafe(nbytes)


def hash_token(token):
    """Digest under which a high-entropy secret is stored and looked up."""
    return hashlib.sha256(token.encode()).hexdigest()


def pkce_s256(verifier):
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def check_pkce(verifier, challenge):
    if not isinstance(verifier, str) or not PKCE_VERIFIER_RE.match(verifier):
        return False
    return consteq(pkce_s256(verifier), challenge or "")


# ----------------------------------------------------------------------
# URIs
# ----------------------------------------------------------------------


def _split(uri):
    """urlsplit() that also validates the port; None for unusable URIs."""
    if not isinstance(uri, str) or not uri or len(uri) > MAX_URI_LENGTH:
        return None
    if any(char.isspace() for char in uri):
        return None
    try:
        parts = urlsplit(uri)
        parts.port  # pylint: disable=pointless-statement
    except ValueError:
        return None
    return parts


def is_loopback_host(hostname):
    return (hostname or "").lower() in LOOPBACK_HOSTS


def is_valid_redirect_uri(uri):
    """Redirect URIs must use https, or http on a loopback host (RFC 8252)."""
    parts = _split(uri)
    if not parts or "#" in uri or not parts.hostname:
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if parts.scheme == "https":
        return True
    return parts.scheme == "http" and is_loopback_host(parts.hostname)


def redirect_uri_matches(registered, requested):
    """Exact match, except the port of loopback redirect URIs (RFC 8252 7.3)."""
    if registered == requested:
        return True
    reg, req = _split(registered), _split(requested)
    if not reg or not req:
        return False
    return (
        reg.scheme == req.scheme == "http"
        and is_loopback_host(reg.hostname)
        and reg.hostname == req.hostname
        and reg.path == req.path
        and reg.query == req.query
    )


def add_query(uri, params):
    """Append ``params`` to ``uri``, keeping the query it already has."""
    parts = urlsplit(uri)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.extend((key, value) for key, value in params.items() if value is not None)
    return urlunsplit(parts._replace(query=urlencode(query)))


def normalize_uri(uri):
    """Compare resource URIs case-insensitively on scheme and host, and
    regardless of a trailing slash."""
    parts = _split(uri)
    if not parts or not parts.scheme or not parts.netloc:
        return ""
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            parts.query,
            "",
        )
    )


# ----------------------------------------------------------------------
# Signed values
# ----------------------------------------------------------------------


def _signature(secret, scope, body):
    message = ("%s:%s" % (scope, body)).encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def sign(secret, scope, values, max_age):
    """Serialize ``values`` into a URL-safe string signed with ``secret``."""
    payload = dict(values, exp=int(time.time()) + max_age)
    body = json.dumps(payload, sort_keys=True).encode()
    body = base64.urlsafe_b64encode(body).decode().rstrip("=")
    return "%s.%s" % (body, _signature(secret, scope, body))


def verify(secret, scope, signed):
    """The values given to sign(), or None if tampered with or expired."""
    if not isinstance(signed, str) or "." not in signed:
        return None
    body, _sep, signature = signed.rpartition(".")
    if not consteq(signature, _signature(secret, scope, body)):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except ValueError:
        return None
    if not isinstance(payload, dict) or payload.get("exp", 0) < time.time():
        return None
    return payload


# ----------------------------------------------------------------------
# Client ID Metadata Documents
# ----------------------------------------------------------------------


def is_ip_literal(hostname):
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return True


def check_metadata_document_url(url):
    """Whether ``url`` is acceptable as a client_id to fetch metadata from.

    Besides the rules of the Client ID Metadata Document draft, only the
    default https port and host names (no IP literal) are accepted, to limit
    what an attacker can make the server request.
    """
    parts = _split(url)
    if not parts or parts.scheme != "https" or not parts.hostname:
        return False
    if parts.port is not None or "#" in url:
        return False
    if parts.username is not None or parts.password is not None:
        return False
    if is_ip_literal(parts.hostname):
        return False
    segments = {unquote(segment) for segment in parts.path.split("/")}
    if parts.path in ("", "/") or segments & {".", ".."}:
        return False
    return True


def is_public_address(address):
    """Only globally routable addresses may be fetched (SSRF protection)."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        # includes IPv6 addresses carrying a zone index
        return False
    if ip.version == 6 and (
        ip.ipv4_mapped or ip.sixtofour or ip.teredo or ip in NAT64_NETWORK
    ):
        return False
    return ip.is_global


def resolve_host(hostname):
    infos = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    return {info[4][0] for info in infos}


def fetch_metadata_document(url):
    """GET a Client ID Metadata Document.

    Returns ``(document, cache_control)``. Raises ValueError for anything but
    a small JSON document answered directly (no redirect) within the timeout,
    and requests.RequestException for network errors.
    """
    deadline = time.monotonic() + METADATA_DOCUMENT_TIMEOUT
    response = requests.get(
        url,
        timeout=METADATA_DOCUMENT_TIMEOUT,
        allow_redirects=False,
        stream=True,
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
    )
    try:
        if response.status_code != 200:
            raise ValueError("HTTP status %s" % response.status_code)
        content_type = response.headers.get("Content-Type", "")
        content_type = content_type.split(";")[0].strip().lower()
        if content_type != "application/json" and not content_type.endswith("+json"):
            raise ValueError("unexpected content type %r" % content_type)
        size, chunks = 0, []
        for chunk in response.iter_content(chunk_size=1024):
            size += len(chunk)
            if size > METADATA_DOCUMENT_MAX_BYTES:
                raise ValueError("document larger than %s bytes" % size)
            if time.monotonic() > deadline:
                raise ValueError("document not received in time")
            chunks.append(chunk)
        return json.loads(b"".join(chunks)), response.headers.get("Cache-Control", "")
    finally:
        response.close()


def max_age_from_cache_control(header, default=3600, minimum=300, maximum=86400):
    """How long to keep a metadata document, bounded to [minimum, maximum]."""
    header = (header or "").lower()
    if "no-store" in header or "no-cache" in header:
        return minimum
    match = re.search(r"max-age=(\d+)", header)
    seconds = int(match.group(1)) if match else default
    return max(minimum, min(maximum, seconds))
