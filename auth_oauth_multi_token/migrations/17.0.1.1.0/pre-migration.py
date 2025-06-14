def migrate(cr, version):
    cr.execute(
        """
        UPDATE
            res_users
        SET
            oauth_access_token = oauth_master_uuid;
        """
    )
