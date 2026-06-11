-- remove API keys
UPDATE auth_api_key
   SET key = NULL;
