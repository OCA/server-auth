import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-auth_admin_passkey>=16.0dev,<16.1dev',
        'odoo-addon-auth_api_key>=16.0dev,<16.1dev',
        'odoo-addon-auth_api_key_server_env>=16.0dev,<16.1dev',
        'odoo-addon-auth_jwt>=16.0dev,<16.1dev',
        'odoo-addon-auth_jwt_demo>=16.0dev,<16.1dev',
        'odoo-addon-auth_ldaps>=16.0dev,<16.1dev',
        'odoo-addon-auth_oidc>=16.0dev,<16.1dev',
        'odoo-addon-auth_saml>=16.0dev,<16.1dev',
        'odoo-addon-auth_signup_verify_email>=16.0dev,<16.1dev',
        'odoo-addon-auth_user_case_insensitive>=16.0dev,<16.1dev',
        'odoo-addon-base_user_show_email>=16.0dev,<16.1dev',
        'odoo-addon-user_log_view>=16.0dev,<16.1dev',
        'odoo-addon-users_ldap_mail>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
