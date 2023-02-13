This module does several things:

* It hides the login / password form from view. It will be made visible in debug mode, eg. by adding `?debug=1` to your browser's url.

* It disables password login by default - when you try to authenticate with password, you will be refused. However, you can use two types of whitelisting to allow login:

  * If you want to whitelist certain IP's, you can use the `auth_pass_ip_whitelist` parameter:

        # This will allow login attempts from localhost and 192.168.1.7
        auth_pass_ip_whitelist = ["127.0.0.1", "192.168.1.7"]

    If this parameter is not set, it defaults to `["127.0.0.1"]`.

  * If you want to whitelist certain URL's, you can use the `auth_pass_ignore_endpoints` parameter:

        # This will allow login attempts on the below endpoints:
        auth_pass_ignored_endpoints = ["/auth_saml/signin", "/authenticate/oauth1/authorize"]
