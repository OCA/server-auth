We have a group called `Amsterdam` and want it to contain all users from
city of Amsterdam. So we use the membership condition

.. code:: python

   user.partner_id.city == 'Amsterdam'

Now we can be sure every user living in this city is in the right group, and we
can start assigning local menus to it, adjust permissions, etc. Keep in mind
that view overrides can also be restricted by a group id, this gives a lot of
possibilities to dynamically adapt views based on arbitrary properties
reachable via the user record.
