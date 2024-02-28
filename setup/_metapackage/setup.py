import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-auth_api_key',
        'odoo13-addon-auth_from_http_remote_user',
        'odoo13-addon-auth_jwt',
        'odoo13-addon-auth_jwt_demo',
        'odoo13-addon-auth_ldaps',
        'odoo13-addon-auth_oauth_autologin',
        'odoo13-addon-auth_oauth_multi_token',
        'odoo13-addon-auth_oidc',
        'odoo13-addon-auth_saml',
        'odoo13-addon-auth_session_timeout',
        'odoo13-addon-auth_signup_verify_email',
        'odoo13-addon-auth_user_case_insensitive',
        'odoo13-addon-base_user_show_email',
        'odoo13-addon-password_security',
        'odoo13-addon-user_log_view',
        'odoo13-addon-users_ldap_groups',
        'odoo13-addon-users_ldap_mail',
        'odoo13-addon-users_ldap_populate',
        'odoo13-addon-vault',
        'odoo13-addon-vault_share',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
