# LyodVPN — downloads

Public download mirror for the **LyodVPN** client (an AmneziaVPN fork with freeze telemetry).

- **Download page:** https://siddie.github.io/lyodvpn-downloads/
- **Latest binaries:** see [Releases](../../releases/latest)

## What this repo is (and isn't)

This repo contains **no source code**. It exists only to publish compiled installers
publicly and host a simple download page (GitHub Pages) — because the source repo is
private, and a private repo's releases are not publicly downloadable.

Installers are pushed here automatically by the private source repo's CI. The download
page (`index.html`) reads the latest release via the GitHub API and lists per-platform
downloads.

## Platforms

| Platform | Asset |
|----------|-------|
| Windows  | `*.exe` (unsigned — *More info → Run anyway* past SmartScreen) |
| macOS    | `*.pkg` (unsigned — right-click → *Open* past Gatekeeper) |
| Android  | `LyodVPN_<version>_android_arm64.apk` (allow install from this source) |
| Linux    | `*.run` |

> Note: `*.github.io` and github.com are throttled in some censored networks. Treat this
> as one mirror; distribute alternative channels (Telegram bot, direct domains) alongside.
