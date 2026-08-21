Exposes vaults from the `vault` module to portal contacts
(`base.group_portal`), individually end-to-end encrypted like internal
users: each contact holds their own key pair, and the vault's master
key is re-wrapped for them.

Portal contacts can view the entries of vaults shared with them, and,
where granted per contact, edit existing field values, add new fields,
create new entries, edit an entry's URL and expiry date, and download
or upload files attached to an entry. The vault itself, entry names,
and entry/file deletion remain read-only from the portal. Entry tags
are shown, read-only.

Entries can be searched by name, URL, and tag, and filtered by
active/expired status. A contact can also invalidate their own key
pair from the portal.

An optional MFA policy (Settings > Vault) can require two-factor
authentication for portal contacts before granting write access, or
before granting any access at all.
