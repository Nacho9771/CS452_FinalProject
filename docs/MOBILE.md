# My Kitchen Android client

The native Android app is in `mobile/`, built with Kotlin and Jetpack Compose.
This is the first mobile slice of AppFlow, distinct from the temporary browser
helper at `/dev/sign-in`. The backend remains shared with future iOS clients;
this module does not yet implement iOS or shared Kotlin Multiplatform code.

## Design reference and current behavior

The November 27 Facebook/Robinhood references guide **navigation behavior**, not
their branding or unrelated social/trading features. The four destinations remain
Find Recipes, Calendar, Your Recipes, and Profile. The menu stays at the bottom
while each destination scrolls. Icons, labels, selection semantics, and a cranberry
top indicator communicate the active destination. Tap a tab or swipe horizontally
between destinations; vertical movement scrolls the current content. Recipe detail
mode disables tab changes and returns with the visible back arrow or Android Back.
Future card-swiping selection must likewise disable destination paging.

`Theme.kt` uses the hex labels from `colors.jpg`: midnight `#37514D`, cranberry
`#B6594C`, ceramic mug `#DD8E75`, knit sweater `#EEE6DE`, steel blue `#90AEB2`, and
camel coat `#BE845E`. Cream surfaces, green text, serif headings, and rounded
photo cards implement the current visual direction.

Implemented client paths:

- Google sign-in through Android Credential Manager and Firebase Authentication.
- Existing Firebase session restoration, account bootstrap, and private-recipe loading.
- Your Recipes as a two-column staggered photo grid, local title filtering,
  refresh/pagination, loading/empty/error states, and read-only recipe details.
- Original ingredient wording/steps, servings, preparation/cooking times, equipment,
  and an optional source link in details. Missing photos keep a native placeholder.
- Profile greets the user and provides sign-out, which clears displayed private data.

Find Recipes and Calendar show honest coming-next states, not invented results or
planned meals. Mobile recipe creation/editing, saved/loved tabs, onboarding, profile
editing, unit previews, calendar writes, discovery, inactivity timeout, and account
deletion are not implemented in this mobile slice. Use the existing browser helper
to add recipes until the native editor lands. Stored recipes load from the same API;
there is no seeded demo catalog in the running app.

## Setup and build

1. Install [Android Studio](https://developer.android.com/studio), complete the SDK
   wizard, and install Android SDK Platform **36** and platform-tools. A newer SDK
   alone doesn't replace the pinned compile platform. Gradle can install the pinned
   platform/build-tools once their SDK licenses have been accepted in the wizard.
2. Open **this repository's `mobile` folder** in Android Studio. Allow Gradle sync.
   The project pins AGP 8.13.2, Kotlin/Compose compiler 2.2.21, Gradle 8.13, and a
   Compose BOM; don't update one component in isolation to fix a random warning.
3. Use a compatible Gradle JDK, preferably **17**. The newly installed Studio bundles
   Java 25, which is too new for this pinned Gradle version. A checksum-verified
   project-local JDK 17 is under `.local/jdk17/` when downloaded by this session.
   `mobile/dev.ps1` finds it automatically if `JAVA_HOME` is unset. In Android Studio,
   set **Settings → Build, Execution, Deployment → Build Tools → Gradle → Gradle JDK**
   to that JDK 17 directory. This doesn't change the IDE's own runtime.
4. In Device Manager, create/start a phone emulator with a **Google Play** system
   image. Sign into Google on the emulator when needed. Firebase Google sign-in
   needs a usable Google account and Play Services; a plain AOSP image isn't enough.

From the repository directory in PowerShell:

```powershell
.\mobile\dev.ps1 build       # assembleDebug and lintDebug
.\mobile\dev.ps1 devices     # list connected devices
.\mobile\dev.ps1 run         # installDebug, then launch
.\mobile\dev.ps1 test        # UI instrumentation tests on a running emulator
.\mobile\dev.ps1 signing     # display the debug signing certificate fingerprint
```

`dev.ps1` writes the local SDK path into ignored `mobile/local.properties`. If
you supplied a different `JAVA_HOME`, it takes priority; choose a compatible JDK.
The official Gradle wrapper JAR was checked against Gradle's published SHA-256,
and the wrapper properties also pin the distribution checksum.

## Firebase Android registration

The Android application ID is **`com.mykitchen.app`**. It is registered in the
existing Firebase project as **My Kitchen Android**. The public client file
`mobile/app/google-services.json` is local and ignored by Git. It does not contain
the Firebase Admin private key or MongoDB credentials. Never copy the backend's
service-account JSON or `.env` into an Android resource or asset directory.

After the first debug build generates a debug keystore:

1. Run `.\mobile\dev.ps1 signing` and copy the debug variant's **SHA1** fingerprint.
2. Register it and refresh the public client config:

   ```powershell
   uv run python scripts/configure_android_firebase.py --sha1 "YOUR_DEBUG_SHA1"
   ```

   Alternatively, add the fingerprint under Firebase Project settings → Your apps
   → My Kitchen Android → SHA certificate fingerprints, download the updated
   `google-services.json`, and place it in `mobile/app/`.
3. Rebuild/install the app. Google must remain enabled in Firebase Authentication.
   The Google Services plugin generates `default_web_client_id`, used by Credential
   Manager's Google button flow. This is the **web OAuth client ID**, not the Android
   OAuth client ID or Firebase app ID.

Without the config file, the app can compile and show its UI, but signing in reports
that the build isn't configured. Debug fingerprint registration is specific to the
development keystore; release signing needs separate setup before distribution.

## Backend connection

Run the backend in a separate terminal:

```powershell
uv run cs-452-finalproject
```

The debug build uses `http://10.0.2.2:8000`: Android Emulator's address for the
host computer's loopback interface. `localhost` inside Android refers to Android,
not the Windows backend. The app permits development HTTP only for the explicit
local debug hosts; release builds retain normal HTTPS requirements. The release
URL is deliberately unusable (`api.example.invalid`) until real hosting is chosen.

For a physical device, one development option is `adb reverse tcp:8000 tcp:8000`
plus a debug base URL of `http://127.0.0.1:8000`. Do not widen network access or
disable certificate verification to work around endpoint mistakes.

Every account/recipe request gets a current Firebase ID token from the SDK and
sends it in the Authorization header. No token/password logging interceptor is
installed. OkHttp runs on `Dispatchers.IO`, outside the UI thread. The backend
verifies token/provider/revocation and filters MongoDB data by that user.

## Follow and personalize the code

| Change | Starting point |
|---|---|
| Color palette | `mobile/app/src/main/java/com/mykitchen/app/ui/Theme.kt` |
| Bottom menu, titles, cards, details, upcoming-tab states | `MainActivity.kt` |
| Selected tab and horizontal paging | `KitchenApp`, `BottomMenu`, `Destination` in `MainActivity.kt` |
| Loading, filtering inputs, restored account, sign-out state | `KitchenViewModel.kt` |
| Google button and Firebase token | `auth/GoogleSession.kt` |
| API paths, response decoding, network errors | `data/KitchenApi.kt` |
| Dependencies and development API URL | `mobile/app/build.gradle.kts` |
| Tap/swipe selection checks | `mobile/app/src/androidTest/.../NavigationTest.kt` |

One request travels: `MainActivity` button → ViewModel coroutine → GoogleSession
ID token → KitchenApi/OkHttp → FastAPI → Firebase verifier → MongoDB → JSON parser
→ StateFlow → Compose redraw. The selected destination and search text survive
ordinary recomposition; list data is reloaded through the ViewModel. Android
process death, a durable offline outbox, and a weeks-long inactivity policy need
separate work; Firebase session persistence alone isn't that policy.

`KitchenNavigationPreview` renders the shell without a running backend or an
Activity-bound login. Use Compose Preview for layout iteration, then an emulator
for real gestures, image loading, authentication, and network behavior.

## Verification status

On November 27, `mobile/dev.ps1 build` passed APK assembly and Android lint
(0 errors; remaining warnings primarily concern newer dependency versions,
resource lookup, and backup configuration). The APK was installed and launched
on `Medium_Phone_API_37.0`; the signed-out screen and bottom menu were visually
inspected. Firebase Android registration, debug SHA-1 registration, and refreshed
local configuration completed; the config includes Android and web OAuth clients.

The first instrumentation run failed inside the old transitive Espresso library
because `InputManager.getInstance` is unavailable on this emulator. The test setup
now explicitly uses Espresso 3.7.0 and runner 1.7.0. The rerun passed **both tests**:
four-tab tap/swipe selection, and source ingredient text plus the recipe-detail
navigation lock/back path. These use isolated UI fixture data, not a Firebase
login. See `mobile/app/build/reports/androidTests/connected/debug/` for the report.

Real Android Google sign-in and private-recipe network loading still require a
manual login check. Compiling an APK and navigation tests do not prove those paths
or the final onboarding flow. The setup script passed Python lint and formatting.
