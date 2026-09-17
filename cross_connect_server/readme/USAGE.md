First of all after installing the module, you need to configure a fastapi endpoint.

In order to do that, you need to go to the menu `FastAPI > FastAPI Endpoints` and create
a new endpoint for the client to connect to.

Fill the fields with the endpoint's information :

- App: `cross_connect`
- Cross Connect Allowed Groups: The groups that will be allowed to be selected for the
  clients groups.

Then for each client, you will have to add an entry in the `Cross Connect Clients`
table.

An api key will be automatically generated for each client, this is the key that you
will have to provide to the client in order for them to connect to the server. You will
also have to choose the groups that this client will be able to give to its users.
