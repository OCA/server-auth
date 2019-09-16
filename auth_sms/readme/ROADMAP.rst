* add a config wizard to configure parameters
* add a button to send another code
* make SMS codes time out (currently they live as long as the session they were
  generated for)
* make being able to turn on 2FA depend on some security group
* create some auth_mfa_code module and move a lot of code there to have a
  common base for all MFA modules that generate some extra code to fill in
