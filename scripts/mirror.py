#!/usr/bin/env python3
"""Writes releases.json for the download page and copies the newest releases to a
public Google Drive folder. Runs in .github/workflows/mirror.yml.

Why: the page read the release list from api.github.com in the browser. In Russia
that request fails (a blocked or throttled host, or the limit of 60 requests per
hour for many users behind one shared IP), so the page showed no files. The page
now reads releases.json from its own site (github.io), and each file has a second
download link on Google Drive, because GitHub downloads in Russia are slow or
blocked. GitHub stays the source.

The Drive folder holds the files of the newest release only, directly in the folder
and with no subfolders (owner, 2026-11-09): a user who opens the folder link sees one
installer for each platform, and each file name holds the version. The older releases
stay on GitHub only.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
REMOTE = os.environ["DRIVE_REMOTE"]          # for example drive:LyodVPN
LIST_LENGTH = 15
OUT = Path("releases.json")
RCLONE_DIR_NOT_FOUND = 3


def github(path: str) -> list | dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def rclone(*args: str) -> str:
    r = subprocess.run(["rclone", *args], text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"rclone {' '.join(args)} failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout


def drive_entries() -> list[dict]:
    """Every file and folder directly in the Drive folder."""
    return json.loads(rclone("lsjson", REMOTE))


def drive_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def main() -> None:
    releases = [
        rel for rel in github(f"releases?per_page={LIST_LENGTH + 5}")
        if not rel["draft"] and not rel["prerelease"]
    ][:LIST_LENGTH]
    if not releases:
        sys.exit("no published release")
    newest = releases[0]
    newest_assets = [a for a in newest["assets"] if a["state"] == "uploaded"]
    names = {a["name"] for a in newest_assets}

    # The folder is shared as "anyone with the link"; the files in it inherit it.
    rclone("mkdir", REMOTE)
    folder_url = rclone("link", REMOTE).strip()

    # First copy the new files, then delete the old ones, so the folder always holds
    # one complete version.
    have = {e["Name"]: e for e in drive_entries() if not e["IsDir"]}
    for a in newest_assets:
        if a["name"] not in have or have[a["name"]]["Size"] != a["size"]:
            print(f"copy {a['name']} ({a['size']} B) to Drive", flush=True)
            rclone("copyurl", a["browser_download_url"], f"{REMOTE}/{a['name']}")
    on_drive = {}
    for e in drive_entries():
        if e["IsDir"]:
            print(f"remove Drive folder {e['Name']}", flush=True)
            rclone("purge", f"{REMOTE}/{e['Name']}")
        elif e["Name"] not in names:
            print(f"remove old Drive file {e['Name']}", flush=True)
            rclone("deletefile", f"{REMOTE}/{e['Name']}")
        else:
            on_drive[e["Name"]] = e
    for a in newest_assets:
        if a["name"] not in on_drive or on_drive[a["name"]]["Size"] != a["size"]:
            sys.exit(f"Drive copy of {a['name']} is missing or has the wrong size")

    out_releases = []
    for rel in releases:
        is_newest = rel is newest
        assets = [a for a in rel["assets"] if a["state"] == "uploaded"]
        out_releases.append({
            "tag": rel["tag_name"],
            "name": rel["name"] or rel["tag_name"],
            "published_at": rel["published_at"],
            "html_url": rel["html_url"],
            "assets": [{
                "name": a["name"],
                "size": a["size"],
                "updated_at": a["updated_at"],
                "github_url": a["browser_download_url"],
                "drive_url": drive_url(on_drive[a["name"]]["ID"]) if is_newest else None,
            } for a in assets],
        })

    OUT.write_text(json.dumps(
        {"drive_folder_url": folder_url, "releases": out_releases},
        ensure_ascii=False, indent=1,
    ) + "\n")


if __name__ == "__main__":
    main()
