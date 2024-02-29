# © 2024 Florian Kantelberg - initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Before the migration the iterations were hardcoded to 4000
    _logger.info("Setting iterations for previous records")

    cr.execute("UPDATE vault_share SET iterations = 4000 WHERE iterations IS NULL")
