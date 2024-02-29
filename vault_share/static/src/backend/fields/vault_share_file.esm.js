/** @odoo-module alias=vault.share.file **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import VaultFile from "vault.file";
import VaultShareMixin from "vault.share.mixin";
import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export default class VaultShareFile extends VaultShareMixin(VaultFile) {}

VaultShareFile.displayName = _lt("Vault Share Field");
VaultShareFile.template = "vault.FileShareVault";

registry.category("fields").add("vault_share_file", VaultShareFile);
