To apply this authentication system to your user, you must set:

- 'device_code' with the code stored in your external id (the code of the rfid, barcode,...)
- 'is_allowed_to_connect_with_device' must be set to True

To connect with this authentication system:

- go to the odoo web site
- click on 'Sign in'
- Below the login button, click on 'Log in with your Device'
- A modal will appear and insert your device code in the field
- click on 'Log in'

If the device_code is correct and the user allowed to connect with it, you should be connected.
else your are redirected to the login page with an error giving information about what happened
