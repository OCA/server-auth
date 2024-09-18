# Copyright 2024 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(cr, registry):
    # Set password date for already existing users
    cr.execute(
        """
        UPDATE
            res_users
        SET
            password_write_date = NOW() at time zone 'UTC'
        WHERE
            password_write_date IS NULL;
    """
    )
