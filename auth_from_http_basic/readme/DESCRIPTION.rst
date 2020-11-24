In an environment where several web applications authenticate against the same
source, the simplest way to attain single sign on would be to have the
webserver handle authentication and pass the login information via HTTP headers
to the application it proxies.

This addon allows for this setup. Technically, it picks up the HTTP
Authorization header, extracts a username and a password and tries to login
into the first database found in the database list.

If you have to set a specific database, possibly depending on the login
provided, use the addon dbfilter_from_header.

Since BASIC auth uses just the Base64 encoding of ID and password it is not
safe to use over HTTP. Thus when using you should opt for HTTPS
