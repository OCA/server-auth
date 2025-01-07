def migrate(cr, version):
    """
    Updates the 'inactive_session_time_out_ignored_url' parameter
    in the 'ir_config_parameter' table during migration.
    """
    cr.execute(
        """
        UPDATE ir_config_parameter
        SET value = '/calendar/notify,/websocket'
        WHERE key = 'inactive_session_time_out_ignored_url'
        """
    )
