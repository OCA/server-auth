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
        'odoo-addon-auth_saml>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
