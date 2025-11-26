You can use these configuration parameters
(menu `Settings / Technical / Parameters / System Parameters`) that control
this addon behavior:

* ``auth_brute_force.whitelist_remotes`` is a comma-separated list of
  whitelisted IPs. Failures from these remotes are ignored.

* ``auth_brute_force.max_by_ip`` defaults to 50, and indicates the maximum
  successive failures allowed for an IP. After hitting the limit, the IP gets
  banned.

* ``auth_brute_force.max_by_ip_user`` defaults to 10, and indicates the
  maximum successive failures allowed for any IP and user combination.
  After hitting the limit, that user and IP combination is banned.

* ``auth_brute_force.check_remote`` defaults to True, and indicates if it
  it will check the information on http://ip-api.com