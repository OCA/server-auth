import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-auth_api_key>=15.0dev,<15.1dev',
        'odoo-addon-auth_api_key_group>=15.0dev,<15.1dev',
        'odoo-addon-auth_api_key_server_env>=15.0dev,<15.1dev',
        'odoo-addon-auth_ldaps>=15.0dev,<15.1dev',
        'odoo-addon-auth_oauth_multi_token>=15.0dev,<15.1dev',
        'odoo-addon-auth_oidc>=15.0dev,<15.1dev',
        'odoo-addon-auth_saml>=15.0dev,<15.1dev',
        'odoo-addon-auth_session_timeout>=15.0dev,<15.1dev',
        'odoo-addon-auth_signup_partner_company>=15.0dev,<15.1dev',
        'odoo-addon-auth_signup_verify_email>=15.0dev,<15.1dev',
        'odoo-addon-auth_user_case_insensitive>=15.0dev,<15.1dev',
        'odoo-addon-password_security>=15.0dev,<15.1dev',
        'odoo-addon-users_ldap_groups>=15.0dev,<15.1dev',
        'odoo-addon-vault>=15.0dev,<15.1dev',
        'odoo-addon-vault_share>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
