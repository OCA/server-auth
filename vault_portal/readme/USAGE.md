1. Grant portal access to the contact (partner form, "Grant portal
   access").
2. The contact visits `/my/vaults` and clicks "Set up my key" there.
   This works even with zero vaults shared yet: it generates their
   personal key pair, a prerequisite for step 3.
3. A technician adds a line in the desired vault's rights (`right_ids`)
   for the contact's user, with the desired permissions. Only contacts
   who already completed step 2 can be selected.

To revoke access, remove the `vault.right` line; the vault is flagged
for key rotation.

A contact can invalidate their own key pair from `/my/vaults`
("Invalidate my key") if they lose their master password - this
revokes all their existing vault access, exactly like the backend's
own "Invalidate private key" action; a technician must then re-share
access with their new key.

The MFA policy is set in Settings > Vault > "Portal Two-Factor
Authentication Policy" (`none` / `write` / `read`).
