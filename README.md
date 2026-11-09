# LyodVPN — downloads

Public download mirror for the **LyodVPN** client (an AmneziaVPN fork with freeze telemetry).

- **Download page:** https://siddie.github.io/lyodvpn-downloads/
- **Latest binaries:** see [Releases](../../releases/latest)

## What this repo is (and isn't)

This repo contains **no source code**. It exists only to publish compiled installers
publicly and host a simple download page (GitHub Pages) — because the source repo is
private, and a private repo's releases are not publicly downloadable.

Installers are pushed here automatically by the private source repo's CI. Every 15
minutes `.github/workflows/mirror.yml` (`scripts/mirror.py`) writes `releases.json` and
copies the files of the newest release directly into the public Google Drive folder `LyodVPN`
(no subfolders; the files of an older release are deleted there)
(rclone, secret `RCLONE_DRIVE_TOKEN`, scope `drive.file`). The download page
(`index.html`) reads `releases.json` from this site, not from api.github.com (which fails
in Russia), and shows a GitHub and a Google Drive button for each file.

## Platforms

| Platform | Asset |
|----------|-------|
| Windows  | `*.exe` (unsigned — *More info → Run anyway* past SmartScreen) |
| macOS    | `*.pkg` (unsigned — right-click → *Open* past Gatekeeper) |
| Android  | `LyodVPN_<version>_android_arm64.apk` (allow install from this source) |
| Linux    | `*.run` |

> Note: github.com downloads are slow or blocked in Russia; the Google Drive folder is the
> second channel. If `*.github.io` itself gets blocked, give users the Drive folder link.
