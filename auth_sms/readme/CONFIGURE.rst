#. Go to Settings/Technical/SMS providers and configure a provider.
   While you can configure multiple ones, the addon will always pick the
   topmost active provider for authorization.
#. On a user, enable the `Use SMS verification` checkbox

The addon understands the following configuration parameters:

   auth_sms.code_chars
      The characters used to generate a code. Default is generated from
      Python's string.ascii_letters + string.digits.

      You can repeat characters here to make some more or less probable to be
      used.

   auth_sms.code_length
      The length of a code to be sent to the user via SMS. Default is 8.

   auth_sms.rate_limit_limit, auth_sms.rate_limit_hours
      The amount of sms to send for one user within a certain amount of time.
      Default is to send at most 10 SMS within 24 hours.
