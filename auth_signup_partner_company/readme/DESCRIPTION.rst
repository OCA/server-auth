This module assigns company to the user and its partner newly created through portal signup.

Odoo's standard behavior when a new portal user signs up:

* User's company is taken from the template user.
* Partner which links to the new user does not have a company assigned.

This behavior is problematic under multi-company, multi-website settings where partners
should be seggregated between the companies, and this module intends to fix this issue.
