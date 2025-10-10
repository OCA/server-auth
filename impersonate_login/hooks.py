# Copyright 2024 360ERP (<https://www.360erp.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging


def pre_init_hook(env):
    """
    Pre-create the impersonated_author_id column in the mail_message table
    to prevent the ORM from invoking its compute method on a large volume
    of existing mail messages.
    """
    logger = logging.getLogger(__name__)
    logger.info("Add mail_message.impersonated_author_id column if not exists")
    env.cr.execute(
        "ALTER TABLE mail_message "
        "ADD COLUMN IF NOT EXISTS "
        "impersonated_author_id INTEGER"
    )
