// Copyright (C) 2017 Joren Van Onder

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as
// published by the Free Software Foundation; either version 3 of the
// License, or (at your option) any later version.

// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.

// You should have received a copy of the GNU Lesser General Public
// License along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
// 02110-1301 USA

odoo.define('auth_u2f.u2f', function (require) {
    'use strict';

    var CrashManager = require('web.CrashManager');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var registry = require('web.field_registry');
    var framework = require('web.framework');

    var _t = core._t;

    CrashManager.include({
        rpc_error: function(error) {
            if (error.data.name === 'odoo.addons.auth_u2f.models.http.U2FAuthenticationError') {
                return framework.redirect('/web/u2f/login?redirect=' +
                                          encodeURIComponent(window.location.href.replace(window.location.origin, '')));
            } else {
                return this._super.apply(this, arguments);
            }
        },
    });

    var FieldU2F = AbstractField.extend({
        className: 'o_field_u2f',
        supportedFieldTypes: ['char'],

        init: function () {
            this._super.apply(this, arguments);
            this.u2f_error_code = false;
        },

        /**
         * See https://developers.yubico.com/U2F/Libraries/Client_error_codes.html
         */
        _get_error_message: function () {
            var code = this.u2f_error_code;
            if (code === 1) {
                return _t('An unknown error occurred.');
            } else if (code === 2) {
                return _t('A bad request was sent to your browser. This can happen when the URL\
 you\'re on is not web.base.url or when this page is not served over HTTPS.');
            } else if (code === 3) {
                return _t('U2F is not supported by this client.');
            } else if (code === 4) {
                return _t('This device is already registered for this user.');
            } else {
                return _t('An unknown error occurred.');
            }
        },

        _render: function () {
            if (! this.u2f_error_code) {
                this.$el.css('color', '');
                if (this.value) {
                    this.$el.html('<i class="fa fa-check-circle"></i> ' + _t('Scanned key.'));
                } else {
                    this.$el.html('<i class="fa fa-spinner fa-spin"></i> ' + _t('Insert your security key and tap the button or gold disk.'));
                }
            } else {
                this.$el.css('color', 'red');
                this.$el.html('<i class="fa fa-spinner fa-spin"></i> ' + this._get_error_message()
                              + ' (error code: ' + this.u2f_error_code + ')');
            }

            return this._super.apply(this, arguments);
        },

        _renderEdit: function () {
            var self = this;

            // an error code of 4 (bad request) most likely won't resolve itself, so don't retry
            if (this.value || this.u2f_error_code === 2) {
                return;
            }

            this._rpc({
                model: 'res.users',
                method: 'u2f_get_registration_challenge',
            }).then(function (challenge_data) {
                // ideally this register request would be cancelled
                // when this field widget is destroyed but the u2f lib
                // doesn't seem to be able to do that at the moment.
                u2f.register(challenge_data.appId,
                             challenge_data.registerRequests,
                             challenge_data.registeredKeys.map(JSON.parse),
                             function (data) {
                                 if (data.errorCode) {
                                     self.u2f_error_code = data.errorCode;
                                     self._render();
                                 } else {
                                     self.u2f_error_code = false;
                                     self._setValue(JSON.stringify(data));
                                     self._render();
                                 }
                             },
                             0); // timeout of 0 seconds means don't timeout
            });
        },
    });

    registry.add('u2f_scan', FieldU2F);

    return {
        FieldU2F: FieldU2F,
    };
});
