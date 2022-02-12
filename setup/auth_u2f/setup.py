import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'u2flib_server': 'u2flib_server',
            }
        }
    },
)
