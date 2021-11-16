Set the values in system configuration parameters for the following:

* activate_verification_code: activate this module
* verification_code_expiry: the time in minutes that a user can use a verification code
  before it expires

For avoiding excessive generation of codes:

* max_verif_code_generation_delay: time period
* max_verif_code_generation: number of code generation allowed

For avoiding excessive attempts at code usage:

* max_verif_code_attempts_delay: time period
* max_verif_code_attempts: number of code verification attempts allowed
