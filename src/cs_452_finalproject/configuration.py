"""Load only this app's named settings, without logging any secret values."""

import os

from dotenv import load_dotenv

SETTINGS = (
    "FIREBASE_PROJECT_ID",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "MONGODB_URI",
    "MONGODB_DATABASE",
    "MONGODB_USERNAME",
    "MONGODB_PASSWORD",
    "FIREBASE_ID_TOKEN",
    "FIREBASE_WEB_API_KEY",
    "FIREBASE_WEB_APP_ID",
    "FIREBASE_AUTH_DOMAIN",
    "ENABLE_DEV_SIGNIN",
)


def load_environment():
    # Already-running Windows applications may have an old environment snapshot.
    # Read just our explicitly named User settings; never enumerate secret values.
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                for name in SETTINGS:
                    if name in os.environ:
                        continue
                    try:
                        value, _ = winreg.QueryValueEx(key, name)
                    except FileNotFoundError:
                        continue
                    if isinstance(value, str):
                        os.environ[name] = value
        except FileNotFoundError, PermissionError:
            pass
    # Priority: process environment, Windows User settings, then local .env.
    load_dotenv()
