# -*- coding: utf-8 -*-
# pylint: disable=W7935, W7936, W0403

import click
import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

import json

from common import (
    UID, PWD,
    CLIENT_ID, CLIENT_SECRET,
    TOKEN_DATA_FILE, DEFAULTS_DATA_FILE,
    DOMAIN, REALM,
    GET_TOKEN_PATH,
    do_request
)

default_conf = {
    'domain': DOMAIN,
    'realm': REALM,
    'username': UID,
    'password': PWD,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
}

if os.path.isfile(DEFAULTS_DATA_FILE):
    click.echo('Loading defaults from %s' % DEFAULTS_DATA_FILE)
    with open(DEFAULTS_DATA_FILE, 'r') as ff:
        default_conf = json.loads(ff.read())


@click.command()
@click.option(
    '--domain',
    default=default_conf['domain'],
    prompt='domain',
)
@click.option(
    '--realm',
    default=default_conf['realm'],
    prompt='realm',
)
@click.option(
    '--username',
    prompt='Username',
    help='Username to authenticate.',
    default=default_conf['username'])
@click.option(
    '--password',
    prompt='Password',
    default=default_conf['password'])
@click.option(
    '--client_id',
    prompt='Client ID',
    help='Keycloak client ID.',
    default=default_conf['client_id'])
@click.option(
    '--client_secret',
    prompt='Client secret',
    help='Keycloak client secret.',
    default=default_conf['client_secret'])
def get_token(**kw):
    """Retrieve auth token."""
    data = kw.copy()
    data['grant_type'] = 'password'
    token = _get_token(data)
    data['token'] = token
    with open(TOKEN_DATA_FILE, 'w') as ff:
        ff.write(json.dumps(data))
        click.echo('Token saved to %s' % TOKEN_DATA_FILE)
    with open(DEFAULTS_DATA_FILE, 'w') as ff:
        ff.write(json.dumps(data))
        click.echo('Defaults saved to %s' % DEFAULTS_DATA_FILE)
    return token


def _get_token(data):
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    url = urljoin(data['domain'], GET_TOKEN_PATH.format(realm=data['realm']))
    resp = do_request('post', url, data=data, headers=headers)
    click.echo('Access token:')
    click.echo(resp.json()['access_token'])
    return resp.json()['access_token']


if __name__ == '__main__':
    get_token()
