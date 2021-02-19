Define mappings in Settings / General Settings / Integrations / LDAP Authentication / LDAP Server

Decide whether you want only groups mapped from LDAP (`Only LDAP groups` checked) or a mix of manually set groups and LDAP groups (`Only LDAP groups` unchecked).
Setting this to "no" will result in users never losing privileges when you remove them from a LDAP group, so that's a potential security issue.
It is still the default to prevent losing group information by accident.
If set to "Yes", you need to make sure each user has at least on of the "User types" groups

For active directory, use LDAP attribute 'memberOf' and operator 'contains'. Fill in the DN of the windows group as value and choose an Odoo group users with this windows group are to be assigned to.

For posix accounts, use operator 'query' and a value like::

    (&(cn=bzr)(objectClass=posixGroup)(memberUid=$uid))

The operator query matches if the filter in value returns something, and value
can contain ``$attribute`` which will be replaced by the first value of the
user's LDAP record's attribute named `attribute`.
