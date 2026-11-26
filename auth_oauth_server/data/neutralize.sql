-- a copy of the database must not accept the tokens of the original
UPDATE oauth_server_authorization
   SET revoked = true, revoked_reason = 'admin'
 WHERE revoked IS NOT true;
DELETE FROM oauth_server_refresh_token;
UPDATE auth_jwt_validator
   SET secret_key = md5(random()::text || clock_timestamp()::text)
                 || md5(random()::text || clock_timestamp()::text)
 WHERE user_id_strategy = 'oauth_server';
