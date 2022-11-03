import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'u2flib_server': [
                    'python-u2flib-server',
                    # _EllipticCurvePublicKey' object has no attribute 'verifier'
                    # these are deprecated in cryptography, so auth_u2f needs to
                    # be updated to use verify() instead
                    'cryptography<37',
                ]
            }
        }
    },
)
