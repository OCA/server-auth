import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-auth_api_key',
        'odoo12-addon-auth_ldap_attribute_sync',
        'odoo12-addon-auth_ldaps',
        'odoo12-addon-base_user_show_email',
        'odoo12-addon-users_ldap_groups',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
