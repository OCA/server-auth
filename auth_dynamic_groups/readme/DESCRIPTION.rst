This module allows defining groups whose membership is a set dynamically.

This can be based on a condition expressed as python code and / or on the
categories attributed to the partner/user.

In addition this module allows for easy extention to add other methods to
determine group membership.

To define a new way to determine group membership, add a field named
`dynamic_method_<something>` to the res.groups model, and a corresponding
method `dynamic_method_<something>_check`. Compare the fields/methods called
`dynamic_method_formula[_check]` and `dynamic_method_category[_check]`
to see how this is done.

Criteria can be combined. The methods on res.groups define wether a user
satisfies some test, the value of the corresponding field on res.groups
determine wether the condition will lead to exclusion of the group, inclusion
of the group, be ignored, or needs to be combined with other conditions.

If any condition excludes a user from a group, this always 'wins'

Finally a group can be marked as being filled automatically. For instance
groups that are maintained from an ldap connection can in this way be
prevented from manual editting.
