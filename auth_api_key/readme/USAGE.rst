To apply this authentication system to your http request you must set 'api_key'
as value for the 'auth' parameter of your route definition into your controller.

.. code-block:: python

    class MyController(Controller):

        @route('/my_service', auth='api_key', ...)
        def my_service(self, *args, **kwargs):
            pass

It is possible to associate an inactive user to the key by adding an optional attribute to your configuration parameter:
  * allow_inactive_user: True or False

Be careful if you use this feature as the problem with inactive users is that they will be removed from the group that they are in as soon as you edit the user list on an ir.group.
The m2m widget for users on the group will not include them - as they are inactive, so if you changes the list, it will remove it.