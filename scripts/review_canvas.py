"""Read course teaching material into a git-ignored local reference file.

Run with CANVAS_API_KEY in the environment. Reads only course content, never
grades, submissions, messages, or rosters. Does not send the key to external links.
"""

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests

BASE = "https://byu.instructure.com/api/v1/courses/35462"


def fetch(path: str, *, paginated: bool = False):
    url = f"{BASE}/{path}"
    result = []
    while url:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "byu.instructure.com":
            raise ValueError("Refusing to send a Canvas credential to another host")
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {os.environ['CANVAS_API_KEY']}"},
            timeout=30,
            allow_redirects=False,
        )
        if response.status_code != 200:
            # Do not print response headers or signed resource URLs.
            return {"unavailable": response.status_code}
        data = response.json()
        if not paginated:
            return data
        result.extend(data)
        url = response.links.get("next", {}).get("url")
    return result


def main():
    if not os.environ.get("CANVAS_API_KEY"):
        raise SystemExit("Set CANVAS_API_KEY before running this script.")
    content = {}
    for resource in ("modules", "assignments", "pages", "files"):
        content[resource] = fetch(f"{resource}?per_page=100", paginated=True)
    content["module_items"] = []
    content["page_bodies"] = []
    for module in content["modules"]:
        items = fetch(f"modules/{module['id']}/items?per_page=100", paginated=True)
        content["module_items"].append({"module": module["name"], "items": items})
        if isinstance(items, list):
            for item in items:
                if item.get("type") == "Page":
                    content["page_bodies"].append(fetch(f"pages/{item['page_url']}"))
    destination = Path(__file__).resolve().parents[1] / ".local" / "canvas-course.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(content, indent=2), encoding="utf-8")
    for key, value in content.items():
        print(f"{key}: {len(value) if isinstance(value, list) else value}")
    print("Saved course content under .local/ (excluded from Git).")


if __name__ == "__main__":
    main()
