import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-auth_admin_passkey',
        'odoo14-addon-auth_api_key',
        'odoo14-addon-auth_api_key_group',
        'odoo14-addon-auth_api_key_server_env',
        'odoo14-addon-auth_dynamic_groups',
        'odoo14-addon-auth_jwt',
        'odoo14-addon-auth_jwt_demo',
        'odoo14-addon-auth_ldaps',
        'odoo14-addon-auth_oauth_multi_token',
        'odoo14-addon-auth_oidc',
        'odoo14-addon-auth_saml',
        'odoo14-addon-auth_session_timeout',
        'odoo14-addon-auth_signup_verify_email',
        'odoo14-addon-auth_user_case_insensitive',
        'odoo14-addon-password_security',
        'odoo14-addon-user_log_view',
        'odoo14-addon-users_ldap_groups',
        'odoo14-addon-users_ldap_mail',
        'odoo14-addon-users_ldap_populate',
        'odoo14-addon-vault',
        'odoo14-addon-vault_share',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
