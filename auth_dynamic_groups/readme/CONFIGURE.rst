Normally group membership is maintained by the administrators. Either manually,
or by granting authorities on the user record.

You can select other criteria by which the membership of groups is maintained.

You can have membership determined by a formula, and/or by the categories
of the partner.

Specify that you want to maintain group membership automatically by marking
a group as dynamic. You can then set criteria on the tab page `Dynamic`.

If you want to use a formula you will need to enter a condition that will
need to evaluate to either True or False. Specify the condition, using `user`
which is a browse record of the user in question.

There is a constraint on the field to check for validity of this expression.

If you want to base a group on partner category you can enter the categories
that will include the users linked to a partner to the group.

If a user needs to have a category AND needs to satisfy a certain formula,
specify `use` for both criteria.

If a user needs to EITHER have a category OR needs to satify a formula,
specify `include` for both.

If having a category, or satisfying a formula, should exclude a user from a
group, specify `exclude` for that criterium.

If a user is excluded from a group, that criterium always has priority.

When you're satisfied, click the button `Refresh` to prefill the group's
members. The condition will be checked now for every user who logs in.
