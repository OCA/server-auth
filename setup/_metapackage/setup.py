import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-server-auth",
    description="Meta package for oca-server-auth Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-auth_keycloak',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 9.0',
    ]
)
