from odoo import models


class IrHttp(models.AbstractModel):
    """Surcharge pour ajouter les traductions du module en front."""

    # region Private attributes
    _inherit = 'ir.http'

    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    # endregion

    # region Fields method
    # endregion

    # region Constraints and Onchange
    # endregion

    # region CRUD (overrides)
    @classmethod
    def _get_translation_frontend_modules_name(cls):
        """Add the module name to the list of module that have frontend translation.

        override :meth:`odoo.addons.http_routing.models.ir_http._get_translation_frontend_modules_name`
        """
        # noinspection PyProtectedMember
        mods = super(IrHttp, cls)._get_translation_frontend_modules_name()
        return mods + ['password_security']
    # endregion

    # region Actions
    # endregion

    # region Model methods
    # endregion
