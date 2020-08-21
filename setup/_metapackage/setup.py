import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-auth_admin_passkey',
        'odoo12-addon-auth_api_key',
        'odoo12-addon-auth_from_http_remote_user',
        'odoo12-addon-auth_ldap_attribute_sync',
        'odoo12-addon-auth_ldaps',
        'odoo12-addon-auth_oauth_multi_token',
        'odoo12-addon-auth_saml',
        'odoo12-addon-auth_session_timeout',
        'odoo12-addon-auth_signup_verify_email',
        'odoo12-addon-auth_totp',
        'odoo12-addon-auth_u2f',
        'odoo12-addon-auth_user_case_insensitive',
        'odoo12-addon-base_user_show_email',
        'odoo12-addon-password_security',
        'odoo12-addon-user_log_view',
        'odoo12-addon-users_ldap_groups',
        'odoo12-addon-users_ldap_mail',
        'odoo12-addon-users_ldap_populate',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
