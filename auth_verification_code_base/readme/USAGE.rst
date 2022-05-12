Set the values in system configuration parameters for the following:

* activate_verification_code: activate this module
* verification_code_expiry: time in minutes before a verification code becomes invalid
* verification_code_validity: time in minutes before a user needs to refresh verification

Spam protection:
* max_verif_code_generation_delay: time period
* max_verif_code_generation: number of code generation allowed
* max_verif_code_attempts_delay: time period
* max_verif_code_attempts: number of code verification attempts allowed

e.g for maximum generation/attempts to 5 and their delay to 15,
there will be a rolling period of 15 minutes during which you can
only generate/attempt entry of 5 codes maximum, and further attemps will be blocked
