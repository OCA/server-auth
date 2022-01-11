import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "external_dependencies_override": {
            "python": {
                "jose": "python-jose[cryptography]<3.3",
                "rsa": "rsa==4.5",
            }
        }
    },
)
