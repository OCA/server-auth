import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-auth_brute_force',
        'odoo11-addon-auth_ldaps',
        'odoo11-addon-auth_oauth_multi_token',
        'odoo11-addon-auth_saml',
        'odoo11-addon-auth_session_timeout',
        'odoo11-addon-auth_signup_verify_email',
        'odoo11-addon-auth_totp',
        'odoo11-addon-auth_totp_password_security',
        'odoo11-addon-auth_user_case_insensitive',
        'odoo11-addon-keychain',
        'odoo11-addon-password_security',
        'odoo11-addon-users_ldap_mail',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
