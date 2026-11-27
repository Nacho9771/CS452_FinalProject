# Local Google sign-in and account persistence check

The browser helper at <http://localhost:8000/dev/sign-in> tests the real user path:
Google → Firebase ID token → API ownership checks → MongoDB account and kitchen.
It is a development client, not the final Kotlin mobile interface. It uses the
same existing account routes, without bypassing Firebase or accepting test tokens.

## Setup

The Firebase client **My Kitchen Local Development** was registered in project
`my-kitchen-3bb33`. Its public API key, app ID, and auth domain are saved in `.env`.
This registration doesn't deploy a website or replace the planned Android/iOS apps.
Authentication was subsequently initialized and Google sign-in enabled. Browser
inspection confirmed a real Google user loaded their account from MongoDB.

1. In [Firebase console](https://console.firebase.google.com/), select My Kitchen.
2. Open **Build → Authentication → Get started**. Enable **Google** under
   **Sign-in method**, choose the support email, and save.
3. Under **Authentication → Settings → Authorized domains**, add `localhost`
   if missing. Use the `localhost` link above consistently. Merely visiting
   `127.0.0.1` does not mean that domain is authorized for Firebase sign-in.
4. `ENABLE_DEV_SIGNIN=1` enables this helper locally. Also set
   `FIREBASE_WEB_API_KEY`, `FIREBASE_WEB_APP_ID`, `FIREBASE_AUTH_DOMAIN`, and
   `FIREBASE_PROJECT_ID`. Restart the API after editing its configuration.
5. Start `uv run cs-452-finalproject`, then open the helper in a regular browser
   that supports Google sign-in popups. If an embedded browser blocks Google,
   use your normal Chrome or Edge window.

The page loads only Firebase App and Auth modules from Google's CDN, pinned to
13.4.0, following the official [CDN setup](https://firebase.google.com/docs/web/alt-setup).
It therefore needs internet access to load those modules and authenticate.

## Test it

The helper now also has **Your Recipes** and a manual recipe editor. See
[private recipe library](RECIPE_LIBRARY.md) for its fields, ownership, retries,
revision checks, and live Atlas verification.

1. Click **Continue with Google** and finish Google's sign-in yourself.
2. The helper calls `POST /api/v1/account` after Firebase signs you in. Existing
   accounts keep their data; a new user gets defaults. Wait for "Account loaded
   from MongoDB" before editing. A Firebase-only success is not storage verification.
3. Save your name, household size, preferred units, and default cooking time.
4. Save owned/not-owned appliance IDs and spices. The illustrated catalog isn't
   available yet; IDs must use lowercase letters, numbers, hyphens, or underscores.
5. Click **Reload saved data**. It asks before replacing any unsaved form edits.
6. Sign out, sign back into the same Google account, and confirm the values return.
   Restarting the API and repeating proves values are not held in process memory.
7. Test another Google account to check isolation with real services. Unit tests
   already cover the ownership boundary, but this live check is separate evidence.

Profile saves preserve fields this small helper does not edit (address, store
branches, cuisine/dietary settings, and onboarding progress). Kitchen saves update
the explicit owned/not-owned lists. A missing appliance remains unanswered.
The helper doesn't overwrite either section with canned sample data.

A stale revision returns **409** and retains your edited form values. Copy those
edits before reloading, then review and reapply them. The helper intentionally
does not auto-retry a conflicting save. Serial actions disable controls while
requests are running.

## Follow the code

| Responsibility | File |
|---|---|
| Loopback/opt-in checks and public config allowlist | `src/cs_452_finalproject/dev_signin.py` |
| Page structure and accessible form labels | `src/cs_452_finalproject/dev_web/sign-in.html` |
| Layout and responsive styling | `src/cs_452_finalproject/dev_web/sign-in.css` |
| Google popup, token headers, form saves, error messages | `src/cs_452_finalproject/dev_web/sign-in.js` |
| Verified identity and account ownership | `account_api.py`, `services.py` |

`initialize()` fetches an allowlisted public config, imports the Firebase client
SDK, and installs the auth-state listener. `signInWithPopup` opens Google's login;
`onAuthStateChanged` loads the account. `api()` gets an ID token from the SDK and
sends it in the Authorization header. Forms reuse the current account revision
and refresh it from each successful response. `showAccount` displays returned
data using text/value properties rather than interpreting user text as HTML.

Firebase Web API keys identify the client project; they are not Admin private
keys. `/dev/firebase-config` explicitly returns four public fields only. It never
returns MongoDB settings, the service-account JSON, or the server environment.
The account disclosure displays profile data, never authentication tokens.

This helper uses **in-memory Firebase session persistence**. Reloading or closing
the page forgets the browser login, so sign in again to test stored account data.
The mobile app's intended persistent login and inactivity policy remain future
work. Sign out here clears the displayed account and forms; it does not delete
MongoDB records or revoke all sessions on other devices.

## Limits and verification

All `/dev` assets/config routes require opt-in plus a loopback client and a
localhost/loopback Host. They return 404 otherwise and aren't listed in OpenAPI.
Don't enable this helper in a public deployment. Account operations continue
to require valid Firebase identity even on a local computer.

Automated route tests check disabled/remote access, file types, the public-field
allowlist, incomplete configuration, and exclusion from OpenAPI. A live Google
popup sign-in requires the user and is not simulated by those tests. Record the
live account-save result separately after doing it.

Useful errors: `auth/configuration-not-found` means initialize Authentication;
`auth/operation-not-allowed` means enable Google; `auth/unauthorized-domain` means
authorize localhost; `auth/popup-blocked` means allow the popup or use a normal
browser. API 401/403/409/422/503 retain their meanings in `FIREBASE_MONGODB.md`.

## Verification on November 27, 2026

All 34 Python tests passed; lint/format checks passed; `node --check` passed for
the helper's JavaScript. Browser inspection at localhost confirmed that the page
renders and its Firebase SDK initializes to "Ready. Continue with Google to connect
your kitchen." The login button is enabled and profile/kitchen forms remain disabled
while signed out. A screenshot confirmed the desktop layout. Full Google sign-in,
account saving, and persistence across reloads remain pending user console setup
and a manual Google login. No live account data was created by these checks.
