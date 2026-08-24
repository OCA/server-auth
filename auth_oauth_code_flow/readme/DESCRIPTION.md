This module provides a high-security implementation of the OAuth2 Authorization Code Flow for Odoo 18. It serves as the essential bridge for modern identity providers (like GitHub) that have deprecated the insecure Implicit Flow.

## The Security Problem: Why Implicit Flow is Risky

Standard Odoo and many older modules rely on the OAuth2 Implicit Flow. In this flow, the access_token is sent directly to the user's browser in the URL fragment 

- Leakage: Tokens are visible in browser history, server logs, and can be intercepted by malicious browser extensions.
    
- Exposure: Sensitive credentials "touch" the client side, increasing the attack surface.

## Authorization Code Flow

This module implements the Authorization Code Flow (access_token_code), which is the industry standard for secure web applications.

- Server-to-Server: The access_token is exchanged in a secure backend POST request between Odoo and the Provider.
    
- Invisible Tokens: Sensitive tokens never appear in the browser URL or history.
    
- PKCE Ready: Supports Proof Key for Code Exchange (PKCE) to prevent authorization code injection attacks.

Key Value for Developers

- Hybrid Support: Works in harmony with the OCA auth_oidc module. It acts as a pre-processor for the token handshake, allowing strict OIDC providers (Keycloak/Cognito) and standard OAuth2 providers (GitHub) to coexist on the same login page.
