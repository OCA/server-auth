import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    add_controller_to_parameter(cr)


def add_controller_to_parameter(cr):
    """Add /longpolling/im_status because it is executed several times (every 50 seconds)"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    new_url = "/longpolling/im_status"
    ignored_path_key = "inactive_session_time_out_ignored_url"
    param = env["ir.config_parameter"]
    old_value = param.get_param(ignored_path_key, "")
    if new_url in old_value:
        _logger.info(
            "%s is included in the parameter %s already.", new_url, ignored_path_key
        )
        return
    new_value = "%s,%s" % (old_value, new_url)
    param.set_param(ignored_path_key, new_value)
    _logger.info(
        "%s was added to the parameter %s successfully.", new_url, ignored_path_key
    )
