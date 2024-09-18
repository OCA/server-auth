def migrate(cr, version):
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
