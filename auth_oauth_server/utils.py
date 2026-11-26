# Copyright 2026 Lorenzo Battistini
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Stateless helpers of the authorization server.

The two functions that reach the network, ``resolve_host`` and
``fetch_metadata_document``, are module-level so that tests can patch them.
Call them as ``utils.resolve_host(...)``, never import them by name.
"""

import base64
import contextlib
import hashlib
import hmac
import http.client
import ipaddress
import json
import re
import secrets
import socket
import ssl
import threading
import time
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from odoo.tools import consteq

TOKEN_BYTES = 32
MAX_URI_LENGTH = 2048
PKCE_VERIFIER_RE = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")
# base64url without padding of a SHA-256 digest
PKCE_CHALLENGE_RE = re.compile(r"^[A-Za-z0-9\-_]{43}$")
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
METADATA_DOCUMENT_MAX_BYTES = 5 * 1024
METADATA_DOCUMENT_TIMEOUT = 5
HTTPS_PORT = 443
NAT64_NETWORK = ipaddress.ip_network("64:ff9b::/96")


def generate_token(nbytes=TOKEN_BYTES):
    return secrets.token_urlsafe(nbytes)


def hash_token(token):
    """Digest under which a high-entropy secret is stored and looked up."""
    return hashlib.sha256(token.encode()).hexdigest()


def derive_token(secret, scope, token):
    """A token that only the holder of ``secret`` can derive from ``token``."""
    return _signature(secret, scope, token)


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
        _port = parts.port  # raises ValueError for an invalid port
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
    message = (f"{scope}:{body}").encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def sign(secret, scope, values, max_age):
    """Serialize ``values`` into a URL-safe string signed with ``secret``."""
    payload = dict(values, exp=int(time.time()) + max_age)
    body = json.dumps(payload, sort_keys=True).encode()
    body = base64.urlsafe_b64encode(body).decode().rstrip("=")
    return f"{body}.{_signature(secret, scope, body)}"


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
    infos = socket.getaddrinfo(hostname, HTTPS_PORT, type=socket.SOCK_STREAM)
    return {info[4][0] for info in infos}


def resolve_public_address(hostname):
    """An address of ``hostname``, if all of them are public.

    Raises ValueError otherwise, or if the name does not resolve.
    """
    try:
        addresses = resolve_host(hostname)
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot resolve {hostname}: {error}") from error
    if not addresses or not all(is_public_address(a) for a in addresses):
        raise ValueError(f"{hostname} has addresses that are not public")
    return sorted(addresses)[0]


def fetch_metadata_document(url):
    """GET a Client ID Metadata Document.

    Returns ``(document, cache_control)``. Raises ValueError for anything but
    a small JSON document answered directly (no redirect) by a public
    address within the timeout.

    The connection goes to the address checked, not to a new resolution of
    the name that a DNS rebinding could point to the internal network, and
    is cut when the timeout expires, however slowly the host answers.
    """
    parts = urlsplit(url)
    address = resolve_public_address(parts.hostname)
    connection = http.client.HTTPSConnection(
        parts.hostname, HTTPS_PORT, timeout=METADATA_DOCUMENT_TIMEOUT
    )

    def connect():
        sock = socket.create_connection(
            (address, HTTPS_PORT), METADATA_DOCUMENT_TIMEOUT
        )
        # the handshake after the assignment, so that cut() can interrupt it
        connection.sock = ssl.create_default_context().wrap_socket(
            sock, server_hostname=parts.hostname, do_handshake_on_connect=False
        )
        if expired.is_set():
            raise ValueError("document not received in time")
        connection.sock.do_handshake()

    def cut():
        expired.set()
        # not connected yet (connect() then gives up), or already closed
        with contextlib.suppress(AttributeError, OSError):
            connection.sock.shutdown(socket.SHUT_RDWR)

    connection.connect = connect
    expired = threading.Event()
    timer = threading.Timer(METADATA_DOCUMENT_TIMEOUT, cut)
    timer.start()
    try:
        connection.request(
            "GET",
            urlunsplit(("", "", parts.path, parts.query, "")),
            headers={
                "Accept": "application/json",
                "User-Agent": "Odoo auth_oauth_server",
            },
        )
        return read_metadata_response(connection.getresponse())
    except (OSError, http.client.HTTPException) as error:
        if expired.is_set():
            raise ValueError("document not received in time") from error
        raise ValueError(str(error) or repr(error)) from error
    finally:
        timer.cancel()
        connection.close()


def read_metadata_response(response):
    """The document and Cache-Control header of an http.client response."""
    if response.status != 200:
        raise ValueError(f"HTTP status {response.status}")
    content_type = response.getheader("Content-Type") or ""
    content_type = content_type.split(";")[0].strip().lower()
    if content_type != "application/json" and not content_type.endswith("+json"):
        raise ValueError(f"unexpected content type {content_type!r}")
    body = response.read(METADATA_DOCUMENT_MAX_BYTES + 1)
    if len(body) > METADATA_DOCUMENT_MAX_BYTES:
        raise ValueError(f"document larger than {METADATA_DOCUMENT_MAX_BYTES} bytes")
    return json.loads(body), response.getheader("Cache-Control") or ""


def max_age_from_cache_control(header, default=3600, minimum=300, maximum=86400):
    """How long to keep a metadata document, bounded to [minimum, maximum]."""
    header = (header or "").lower()
    if "no-store" in header or "no-cache" in header:
        return minimum
    match = re.search(r"max-age=(\d+)", header)
    seconds = int(match.group(1)) if match else default
    return max(minimum, min(maximum, seconds))
