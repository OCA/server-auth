-- deactivate all api keys and clear the keys
UPDATE auth_api_key
   SET active = false,
       key = 'neutralized';
