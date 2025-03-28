# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import uuid


# this is needed in case there are multiple users without an oauth_identifier,
# which can happen if the database was migrated over several versions and
# multiple new users have been created in the process. the default
# initialization puts the same value on every record, which is invalid for
# this field (see also pre_init_hook()).
def set_missing_oauth_identifiers(cr):
    cr.execute("select id from res_users where oauth_identifier is null")
    for user_id in cr.fetchall():
        cr.execute(
            "update res_users set oauth_identifier = %s where id = %s",
            (str(uuid.uuid4()), user_id),
        )


def migrate(cr, version):
    set_missing_oauth_identifiers(cr)
