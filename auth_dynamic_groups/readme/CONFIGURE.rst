Normally group membership is maintained by the administrators. Either manually,
or by granting authorities on the user record.

You can select other criteria by which the membership of groups is maintained.

You can have membership determined by a formula, or by the categories of the
partner.

Select `Based on formula` on a group you want to be filled according to
some conditions that you specify on the tab page `Dynamic`.

The condition you enter will need to evaluate to either True or False.
Specify the condition, using `user` which is a browse record of the user in
question.

There is a constraint on the field to check for validity of this expression.

If you select `Based on partner category` for the group type, you can enter
the categories that will include the users linked to a partner to the group.

When you're satisfied, click the button `Refresh` to prefill the group's
members. The condition will be checked now for every user who logs in.
