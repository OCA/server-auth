# Copyright 2026 Antonio Ruban
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from cryptography.fernet import Fernet, InvalidToken

from odoo.tools import config

_logger = logging.getLogger(__name__)

# Cache the Fernet instance to avoid recreating it
_fernet = None
_fernet_initialized = False


def get_fernet():
    global _fernet, _fernet_initialized
    if _fernet_initialized:
        return _fernet

    _fernet_initialized = True
    key = config.get("encryption_key")

    if not key:
        _logger.warning(
            "No 'encryption_key' found in odoo.conf. "
            "Encrypted fields will be stored in plaintext!"
        )
        return None

    try:
        # Validate the key is a valid Fernet key (32 url-safe base64-encoded bytes)
        # Fernet will raise ValueError if invalid
        _fernet = Fernet(key.encode("utf-8"))
    except Exception as e:
        _logger.error(
            "Invalid 'encryption_key' in odoo.conf. Encryption disabled! Error: %s", e
        )
        _fernet = None

    return _fernet


def encrypt(value):
    """Encrypt a string value using Fernet."""
    if not value:
        return value

    f = get_fernet()
    if not f:
        return value  # Fallback: plaintext

    try:
        if isinstance(value, str):
            value = value.encode("utf-8")
        return f.encrypt(value).decode("utf-8")
    except Exception as e:
        _logger.error("Encryption failed: %s", e)
        return value


def decrypt(value):
    """Decrypt a Fernet encrypted string."""
    if not value:
        return value

    f = get_fernet()
    if not f:
        return value  # Fallback: plaintext

    try:
        if isinstance(value, str):
            # Check if it looks like a Fernet token (usually starts with gAAAAAB...)
            if not value.startswith("gAAAAAB"):
                return value

            value = value.encode("utf-8")

        return f.decrypt(value).decode("utf-8")
    except InvalidToken:
        # It wasn't encrypted with this key, or wasn't encrypted at all
        return (
            value if isinstance(value, str) else value.decode("utf-8", errors="ignore")
        )
    except Exception as e:
        _logger.error("Decryption failed: %s", e)
        return (
            value if isinstance(value, str) else value.decode("utf-8", errors="ignore")
        )
