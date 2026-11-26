In recent Odoo versions, the login field is tightly linked to the email
field (the field is displayed with an "Email" label, and it will
populate the email of the user if it contains an "@" character).

Yet for the users who uses a distinct login and email, this is
confusing.

The goal of this module is to untangle (a bit) these two fields. Here
are the changes:

- In the res.users form view:  
  - Display a "Login" label instead of "Email" on the login field
  - Show the currently invisible email field and its label

- In the res.users tree view:  
  - Display the email field next to the login field

- Change the login layout to prompt for a "Login" instead of an "Email"
  (compatible with the web_enterprise layout)
