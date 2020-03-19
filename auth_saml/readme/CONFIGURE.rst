To use this module, you need an IDP server, properly set up. Go through the
"Getting started" section for more information.

Getting started with Authentic2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is quick howto to help setup a service provider that will be able
to use the IDP from Authentic2

We will mostly cover how to setup your rsa keys and certificates


Creating the certs
------------------

Use easy-rsa from the easy-rsa package (or from the openvpn project)

Example script below with comment saying what you should do between each
command:

.. code-block:: bash

    #clean your vars

    source ./vars

    ./build-dh
    ./pkitool --initca

    #change your vars to math a new client cert

    source ./vars

    ./pkitool myclient


Congratulations, you now have a client certificate signed by a shiny new
CA under you own private control.

Configuring authentic
---------------------

We will not describe how to compile requirements nor start an authentic server.

Just log into your authentic admin panel::

  https://myauthenticserver/admin


and create a new "liberty provider".

You'll need to create a metadata xml file from a template (TODO)

You'll need to make sure it is activated and that the default protocol rules
are applied (ie: the requests are signed and signatures are verified)

Configuring Odoo
----------------

#. Go to *Settings > Activate the developer mode*.
#. **Configure your auth provider** going to *Settings > Users & Companies >
   SAML Providers > Create*. Your provider should provide you all that info.
#. Go to *Settings > Users & Companies > Users* and edit each user that will
   authenticate through SAML.
#. Go to the *SAML* tab and fill both fields.
#. Go to *Settings > General settings* and uncheck *Allow SAML users to posess
   an Odoo password* if you want your SAML users to authenticate only
   through SAML.
