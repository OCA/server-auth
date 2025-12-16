// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import {VaultFile, vaultFileField} from "@vault/backend/fields/vault_file.esm";
import VaultShareMixin from "./vault_share_mixin.esm";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class VaultShareFile extends VaultShareMixin(VaultFile) {
    static template = "vault.FileShareVault";
}

export const vaultShareFileField = {
    ...vaultFileField,
    component: VaultShareFile,
    displayName: _t("Vault Share Field"),
};

registry.category("fields").add("vault_share_file", vaultShareFileField);
