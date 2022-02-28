import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "external_dependencies_override": {
            "python": {
                "jose": "python-jose",
            }
        }
    },
    install_requires=[
        "python2-secrets ; python_version<'3.6'",
    ],
)
