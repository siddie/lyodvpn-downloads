#!/usr/bin/env python3
"""Writes releases.json for the download page and copies the newest releases to a
public Google Drive folder. Runs in .github/workflows/mirror.yml.

Why: the page read the release list from api.github.com in the browser. In Russia
that request fails (a blocked or throttled host, or the limit of 60 requests per
hour for many users behind one shared IP), so the page showed no files. The page
now reads releases.json from its own site (github.io), and each file has a second
download link on Google Drive, because GitHub downloads in Russia are slow or
blocked. GitHub stays the source; Drive holds copies of the newest releases only.
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
KEEP = int(os.environ["DRIVE_KEEP_RELEASES"])  # releases with a Drive copy
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


def drive_files(tag: str) -> dict[str, dict]:
    r = subprocess.run(["rclone", "lsjson", f"{REMOTE}/{tag}"], text=True, capture_output=True)
    if r.returncode == RCLONE_DIR_NOT_FOUND:
        return {}
    if r.returncode != 0:
        sys.exit(f"rclone lsjson {REMOTE}/{tag} failed ({r.returncode}): {r.stderr.strip()}")
    return {f["Name"]: f for f in json.loads(r.stdout)}


def drive_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def main() -> None:
    releases = [
        rel for rel in github(f"releases?per_page={LIST_LENGTH + 5}")
        if not rel["draft"] and not rel["prerelease"]
    ][:LIST_LENGTH]
    mirrored = {rel["tag_name"] for rel in releases[:KEEP]}

    # The folder is shared as "anyone with the link"; the files in it inherit it.
    rclone("mkdir", REMOTE)
    folder_url = rclone("link", REMOTE).strip()

    out_releases = []
    for rel in releases:
        tag = rel["tag_name"]
        assets = [a for a in rel["assets"] if a["state"] == "uploaded"]
        on_drive = drive_files(tag) if tag in mirrored else {}
        if tag in mirrored:
            for a in assets:
                have = on_drive.get(a["name"])
                if have is None or have["Size"] != a["size"]:
                    print(f"copy {tag}/{a['name']} ({a['size']} B) to Drive", flush=True)
                    rclone("copyurl", a["browser_download_url"], f"{REMOTE}/{tag}/{a['name']}")
            on_drive = drive_files(tag)
            for a in assets:
                have = on_drive.get(a["name"])
                if have is None or have["Size"] != a["size"]:
                    sys.exit(f"Drive copy of {tag}/{a['name']} is missing or has the wrong size")
        out_releases.append({
            "tag": tag,
            "name": rel["name"] or tag,
            "published_at": rel["published_at"],
            "html_url": rel["html_url"],
            "assets": [{
                "name": a["name"],
                "size": a["size"],
                "updated_at": a["updated_at"],
                "github_url": a["browser_download_url"],
                "drive_url": drive_url(on_drive[a["name"]]["ID"]) if a["name"] in on_drive else None,
            } for a in assets],
        })

    # Drive keeps only the newest KEEP releases (15 GB of free space). Purge moves
    # the folder to the Drive trash; GitHub keeps every release.
    for d in json.loads(rclone("lsjson", "--dirs-only", REMOTE)):
        if d["Name"] not in mirrored:
            print(f"remove old Drive copy {d['Name']}", flush=True)
            rclone("purge", f"{REMOTE}/{d['Name']}")

    OUT.write_text(json.dumps(
        {"drive_folder_url": folder_url, "releases": out_releases},
        ensure_ascii=False, indent=1,
    ) + "\n")


if __name__ == "__main__":
    main()
