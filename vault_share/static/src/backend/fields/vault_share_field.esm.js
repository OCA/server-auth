/** @odoo-module alias=vault.share.field **/
// © 2021-2024 Florian Kantelberg - initOS GmbH
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import VaultField from "vault.field";
import VaultShareMixin from "vault.share.mixin";
import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export default class VaultShareField extends VaultShareMixin(VaultField) {}

VaultShareField.displayName = _lt("Vault Share Field");
VaultShareField.template = "vault.FieldShareVault";

registry.category("fields").add("vault_share_field", VaultShareField);
