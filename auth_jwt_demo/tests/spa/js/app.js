import {Oidc} from "./oidc-client.js";

let client = null;

class InMemoryWebStorageStateStore {
    constructor() {
        this._data = {};
    }

    set(key, value) {
        this._data[key] = value;
        return Promise.resolve();
    }

    get(key) {
        const item = this._data[key];
        return Promise.resolve(item);
    }

    remove(key) {
        const item = this._data[key];
        delete this._data[key];
        return Promise.resolve(item);
    }

    getAllKeys() {
        var keys = Object.getOwnPropertyNames(this._data);
        return Promise.resolve(keys);
    }
}

async function onload() {
    const settings_response = await fetch("/auth_settings.json");
    const settings = await settings_response.json();
    settings.redirect_uri = window.location.href;
    settings.post_logout_redirect_uri = window.location.href;
    // Avoid storing JWT tokens in session storage
    settings.userStore = new InMemoryWebStorageStateStore();
    client = new Oidc.UserManager(settings);
    client.events.addAccessTokenExpiring(refresh);

    const query = window.location.search;
    if (query.includes("code=") && query.includes("state=")) {
        // Process the redirect callback from the identity provider
        const user = await client.signinCallback();
        console.log(user); // Don't do this IRL!
        // Use replaceState to redirect the user away and remove the querystring parameters
        window.history.replaceState({}, document.title, "/");
    }

    updateUI();
}

async function updateUI() {
    const user = await client.getUser();
    const isAuthenticated = Boolean(user);

    document.getElementById("btn-login").disabled = isAuthenticated;
    document.getElementById("btn-logout").disabled = !isAuthenticated;
    document.getElementById("txt-email").textContent = isAuthenticated
        ? user.profile.email || user.profile.sub
        : "(please log in)";
}

async function login() {
    client.signinRedirect();
}

async function logout() {
    client.removeUser();
    updateUI();
}

async function refresh() {
    console.log("refresh token");
    client.startSilentRenew();
}

async function _whoami(endpoint) {
    const user = await client.getUser();
    try {
        const response = await fetch(
            "http://localhost:8069/auth_jwt_demo/keycloak" + endpoint,
            {
                headers: {
                    ...(user && {Authorization: `Bearer ${user.access_token}`}),
                },
            }
        );
        const data = await response.json();
        alert(JSON.stringify(data));
    } catch (error) {
        alert(error);
    }
}

async function whoami() {
    await _whoami("/whoami");
}

async function whoami_public_or_jwt() {
    await _whoami("/whoami-public-or-jwt");
}

export {onload, login, logout, whoami, whoami_public_or_jwt};
