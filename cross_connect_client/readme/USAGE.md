First of all after installing the module, you need to configure the server connection.

In order to do that, you need to go to the menu
`Settings > Technical > Cross Connect > Cross Connect Servers` and create a new server
to connect to.

Fill the fields with the server's information :

- Url: The api root path (e.g. `https://my-remote-odoo.com/api`)
- Api Key: The api-key from the `cross_connect_server` configuration

Then click on the `Sync Cross Connection` button to check if the connection is working
and to sync the remote server's groups.

After that, you will have to affect the remote groups to the local users in order for
them to be able to connect to the remote server.

Once an user has a remote group, a new top level menu will appear in the menu bar with
the Cross Connect Server's name. Clicking on it will redirect the user to the remote
server logged in as the user.

You can change each menu icon (for use with `web_responsive` for instance) by setting
the `Web Icon Data` in the server configuration.
