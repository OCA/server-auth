// Copyright (C) 2017 Joren Van Onder
// Copyright (C) 2019 initOS GmbH

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

odoo.define('auth_u2f.login', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;

    function u2f_challenge () {
        var challenge = document.getElementById('u2f_challenge');
        if (! challenge) {
            return;
        }

        var code_to_error_message = {
            1: _t('An unknown error occured'),
            2: _t('A bad request was sent to your browser. This can happen when the URL\
 you\'re on is not web.base.url or when this page is not served over HTTPS.'),
            3: _t('U2F is not supported by this client.'),
            4: _t('This device is not registered as the default device for this user.'),
        };

        var request = JSON.parse(challenge.value);
        if (request.registeredKeys.length > 0) {
            u2f.sign(
                request.appId,
                request.challenge,
                request.registeredKeys,
                function (data) {
                    if (data.errorCode) {
                        // just retry if this timed out
                        if (data.errorCode !== 5) {
                            $('#error_message').text(code_to_error_message[data.errorCode]);
                        }
                        u2f_challenge();
                    } else {
                        document.getElementById('u2f_token_response').value = JSON.stringify(data);
                        document.getElementById('u2f_login_form').submit();
                    }
                });
        }
    }

    $(document).ready(function () {
        u2f_challenge();
    });
});
