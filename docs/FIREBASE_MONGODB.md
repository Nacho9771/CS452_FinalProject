# Firebase and MongoDB: setup and one complete request

This milestone implements backend account/profile/kitchen operations. The mobile Google sign-in interface is not built yet. Tests use injected test doubles and mocked SDK calls, not fake tokens accepted by the production server. On November 26, Google accepted the local Firebase Admin credential and a live MongoDB Atlas ping succeeded. A real Firebase user ID token and account read/write are still pending, so full end-to-end verification is not complete.

## 1. Firebase Google authentication

The selected project ID is `my-kitchen-3bb33`. A project ID is public configuration; it does not give the server administrator access.

Firebase Authentication proves who signed in; MongoDB stores app data. Firebase's Firestore database is an alternative to MongoDB, not a prerequisite for Firebase Authentication. This implementation follows the original MongoDB direction.

1.  Open the [Firebase console](https://console.firebase.google.com/), select My Kitchen, and open Authentication. Start setup and enable the **Google** sign-in provider. Select the support email Firebase requests and save.
2.  Open **Project settings → Service accounts → Firebase Admin SDK**. For local development, generate a private key and save its JSON file outside this repository. Keep that file private. The backend uses Application Default Credentials to read it. Keep the entire JSON file: do not extract `private_key` or edit its escaped `\n` characters. The SDK parses those line breaks and the accompanying metadata.
3.  Put its full path in `GOOGLE_APPLICATION_CREDENTIALS`, either in the local `.env` or your environment. Never paste the JSON contents into code, docs, or the API. Managed hosting can later use its service identity rather than a downloaded key.

The Firebase Admin SDK verifies the ID token's signature, project, and expiry; we also request revocation/disabled-user checks. The backend accepts the Google provider required by AppFlow. Missing/invalid/expired tokens return 401, a different sign-in provider returns 403, and service/configuration outages return 503. An emulator environment variable is rejected in this adapter so unsigned emulator tokens cannot accidentally be accepted by this configured backend.

**Different credentials serve different purposes:**

| Value | Location/purpose |
|------------------------------------|------------------------------------|
| Firebase project ID | Public identifier of your project. |
| Client Firebase web/API configuration | Used by a future client sign-in interface; not an Admin private key. |
| Service-account private key | Backend only: privileged credential used for Admin SDK operations. |
| Firebase ID token | Short-lived user identity returned after client sign-in; sent as `Authorization: Bearer ...`. |
| MongoDB URI | Backend only: database username/password and deployment connection settings. |

A Google OAuth access token, Firebase custom token, and service-account JSON are not substitutes for the Firebase user ID token expected by our account endpoints.

## 2. MongoDB Atlas

1.  Create/sign into [MongoDB Atlas](https://cloud.mongodb.com/). Create a project for My Kitchen, then select a **free deployment if offered**; avoid accepting paid deployment options unintentionally. Choose a nearby available region.
2.  Create a **database user** for the backend. This differs from your Atlas login. Give it `readWrite` access to the `my_kitchen` database rather than broad admin rights. Keep the generated password private.
3.  Under Network Access, allow the current development computer's public IP. Changes to your network/IP may require updating this entry. Do not open access to all IPs merely to get past a connection error.
4.  Select **Connect → Drivers → Python**, and copy the connection URI into the local `MONGODB_URI` setting. Replace username/password placeholders. URL-encode reserved characters in the password if constructing a URI manually; do not remove TLS.
5.  `MONGODB_DATABASE=my_kitchen` selects the database. The `accounts` collection and the database appear on the first successful account creation; you do not need to pre-populate them manually.

## 3. Local configuration and restart

The Git-ignored `.env` currently records the project ID and database name. Add the two private settings locally (the placeholders below are deliberately unusable):

``` dotenv
FIREBASE_PROJECT_ID=my-kitchen-3bb33
GOOGLE_APPLICATION_CREDENTIALS=C:/private/firebase-service-account.json
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=my_kitchen
```

The normal launcher loads `.env`; existing process environment values take precedence. It also reads this app's named Windows User variables, so settings added after Codex opened are available on the next backend launch. Priority is process environment, then Windows User variables, then `.env`.

You can keep the database credentials separate from the URI:

``` dotenv
MONGODB_URI=mongodb+srv://YOUR-CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_USERNAME=your-database-user
MONGODB_PASSWORD=your-database-password
```

These may be Windows User variables instead of `.env` entries. If using separate credentials, set both. The adapter passes them directly to PyMongo as `username` and `password`, removing any credential placeholders from the URI. Special characters in a separately supplied password need no manual URL encoding. A complete URI still works when the two separate settings are absent. Credentials are runtime configuration; never replace `os.getenv(...)` with a real password.

The relevant path is `configuration.load_environment` → `services.mongo_connection_options` → `MongoClient`. For direct uvicorn launches, import newly changed Windows User settings into that terminal first, or use the normal launcher. Configuration changes require a restart.

If you set Windows User environment variables while Codex/the terminal is already running, existing processes may not see them. Open a new terminal, or explicitly load just these named settings into that PowerShell process:

``` powershell
foreach ($setting in @('GOOGLE_APPLICATION_CREDENTIALS', 'MONGODB_URI')) {
    $settingValue = [Environment]::GetEnvironmentVariable($setting, 'User')
    if ($settingValue) { Set-Item -Path "Env:$setting" -Value $settingValue }
}
uv run cs-452-finalproject
```

If running directly with reload, use `uv run uvicorn cs_452_finalproject.api:app --reload --env-file .env`. Restart after changing environment settings. Do not run two servers on port 8000. The API listens on loopback and is still a development server.

## 4. What each endpoint does

1

| Endpoint | Behavior |
|------------------------------------|------------------------------------|
| `POST /api/v1/account` | Idempotent account creation after Google sign-in; creates defaults only on first use. |
| `GET /api/v1/account` | Reads that user's profile, kitchen, and current revision. Returns 404 before creation. |
| `PUT /api/v1/account/profile` | Replaces the full profile section, including preferences and onboarding step. |
| `PUT /api/v1/account/kitchen` | Replaces the full appliance/spice section. |

There is deliberately no user ID in these URLs or editable bodies. `current_uid` derives it from verified Firebase claims. Trying `?uid=someone-else` does not change the database filter. Authorization must remain in place on future endpoints too.

`Profile` supports names, address, phone, up to three store branches, household size, US/metric display preference, cooking time, cuisines with optional exclusive mode, dietary restrictions with the user's enforcement choice, and an onboarding marker. The marker is a client progress checkpoint, not proof of validated complete onboarding. Defaults are initial development choices and can be edited in `accounts.py`.

For appliances, **missing means unanswered**, `true` means owned, and `false` means explicitly not owned. Safe stable IDs such as `skillet` match the future appliance catalog; the CSV and image catalog are still pending. Spices are a presence list, not a quantity ledger. `spice_setup` distinguishes skipped from provided information.

## 5. Storage and concurrency

One `accounts` document contains the user's bounded profile and kitchen:

``` text
accounts
  _id: verified Firebase UID (unique MongoDB primary key)
  revision: 0, 1, 2, ...
  created_at / updated_at: server timestamps
  profile: {...}
  kitchen: {...}
```

Embedding these small sections gives atomic saves without a multi-document transaction or a risk of creating a user without its kitchen. Growing recipe, calendar, and cooking-event records will use separate collections later.

First creation uses `$setOnInsert`: reconnecting from another device cannot reset the kitchen. The built-in unique `_id` index prevents duplicate accounts; a concurrent-create collision reads the account that won instead.

Every update supplies `expected_revision` from the last GET/POST response. The MongoDB filter includes **both UID and revision**; the same atomic update increments revision. If another device saved first, the API returns **409 Conflict**. Reload, review/merge the changes, and retry deliberately with the new revision. Never automatically overwrite someone's other edit. The revision is shared across profile and kitchen, so saving either invalidates old versions of both sections.

`PUT` replaces a section: omitted fields take their model defaults. When editing one field, send the complete section you last loaded with the edited field changed. It does not replace the other section. Arrays/maps are bounded, and unexpected fields such as a caller-supplied owner ID are rejected.

## 6. Follow a request and experiment

``` text
Google sign-in in the future client
  → Firebase user ID token
  → HTTPBearer reads Authorization
  → FirebaseIdentity verifies token with the Admin SDK
  → current_uid returns the verified user ID
  → account_api calls MongoAccounts
  → MongoDB filters by that ID (and revision for edits)
  → Account response validates the document and returns JSON
```

Put breakpoints in `account_api.current_uid`, `FirebaseIdentity.verify`, and `MongoAccounts.update`. Read the filter before the database call: changing the client's JSON must never change its owner.

With a real ID token already set privately in `$env:FIREBASE_ID_TOKEN`:

``` powershell
$authHeaders = @{Authorization = "Bearer $env:FIREBASE_ID_TOKEN"}
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/account -Headers $authHeaders
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/account -Headers $authHeaders
Invoke-RestMethod -Method Put -Uri http://127.0.0.1:8000/api/v1/account/profile `
    -Headers $authHeaders -ContentType application/json -InFile examples/account-profile.json
Invoke-RestMethod -Method Put -Uri http://127.0.0.1:8000/api/v1/account/kitchen `
    -Headers $authHeaders -ContentType application/json -InFile examples/account-kitchen.json
```

The examples assume a new account at revision 0, then revision 1. Read and adjust `expected_revision` if you've already saved data. Repeat an update with its old revision to observe 409; restart the server and GET again to demonstrate persistence. Repeat using a second signed-in Google user to verify separation on the live services.

## 7. Debugging and limitations

| Symptom | Check |
|------------------------------------|------------------------------------|
| 401 | Correct Bearer header and a current Firebase ID token; check the project and sign-in again. |
| 403 | The token's current provider must be Google. |
| 404 | Create the account first; these routes have no user-ID suffix. |
| 409 | Reload the account revision and review the competing edit. |
| 422 | Inspect field validation; at most three stores, positive household size, and recognized fields. |
| 503 Firebase | Project ID, private credential path, credential permissions, network access, and emulator variable. |
| 503 MongoDB | URI/password, database user permissions, IP allowlist, DNS/TLS, and server availability. |
| `/health` says configured_not_verified | A setting exists; that is not a successful connection or sign-in test. |

The client must eventually sign out through Firebase and clear local sensitive state. Account deletion with the flow's two confirmations, inactivity policy, mobile UI, recipe persistence/publication, device outbox, and a complete production deployment remain future work. No deletion or Firebase admin operation is exposed through the API in this milestone. Don't treat the app as production-ready.

## References

- [Firebase ID token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [Admin SDK credentials](https://firebase.google.com/docs/admin/setup)
- [Atlas getting started](https://www.mongodb.com/docs/atlas/getting-started/)
- [MongoDB atomic conditional updates](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/)