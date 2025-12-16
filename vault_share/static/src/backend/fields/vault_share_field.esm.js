// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultField, vaultField} from "@vault/backend/fields/vault_field.esm";
import VaultShareMixin from "./vault_share_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultShareField extends VaultShareMixin(VaultField) {
    static template = "vault.FieldShareVault";
}

export const vaultShareField = {
    ...vaultField,
    component: VaultShareField,
    displayName: _t("Vault Share Field"),
};

registry.category("fields").add("vault_share_field", vaultShareField);
