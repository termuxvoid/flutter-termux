<p align="center">
  <a href="https://flutter.dev/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://camo.githubusercontent.com/792e3b1f45d4d9822b92db7c2ede63331ce78003c01f45e739af74b6e5083b67/68747470733a2f2f646f63732e666c75747465722e6465762f6c6f676f5f6461726b2e706e67">
      <img alt="Flutter" src="https://camo.githubusercontent.com/792e3b1f45d4d9822b92db7c2ede63331ce78003c01f45e739af74b6e5083b67/68747470733a2f2f646f63732e666c75747465722e6465762f6c6f676f5f6461726b2e706e67">
    </picture>
  </a>
</p>

<h1 align="center">Flutter for Termux</h1>

<p align="center">
  <strong>Run the Flutter SDK natively on Android with Termux.</strong><br>
  Prebuilt, patched, and packaged by <a href="https://github.com/termuxvoid">TermuxVoid</a>.
</p>

<p align="center">
  <a href="https://github.com/termuxvoid/flutter-termux/releases/latest"><img src="https://img.shields.io/github/v/release/termuxvoid/flutter-termux?style=for-the-badge&logo=github&color=02569B&labelColor=0d1117" alt="Latest release"></a>
  <a href="https://github.com/termuxvoid/flutter-termux/releases"><img src="https://img.shields.io/github/downloads/termuxvoid/flutter-termux/total?style=for-the-badge&logo=github&color=02569B&labelColor=0d1117" alt="Downloads"></a>
  <a href="https://github.com/termuxvoid/flutter-termux/issues"><img src="https://img.shields.io/github/issues/termuxvoid/flutter-termux?style=for-the-badge&color=fd7d00&labelColor=0d1117" alt="Issues"></a>
  <a href="https://github.com/termuxvoid/flutter-termux/stargazers"><img src="https://img.shields.io/github/stars/termuxvoid/flutter-termux?style=for-the-badge&color=ffd700&labelColor=0d1117" alt="Stars"></a>
  <img src="https://img.shields.io/badge/Flutter-3.47.8-02569B?style=for-the-badge&logo=flutter&logoColor=white" alt="Flutter 3.47.8">
  <img src="https://img.shields.io/badge/Termux-aarch64%20%7C%20x86__64-000000?style=for-the-badge" alt="Termux aarch64 and x86_64">
</p>

---

## Overview

**Flutter for Termux** provides a ready-to-use Flutter SDK for Termux on Android. The SDK is built from the upstream Flutter source with a small set of Termux compatibility patches, then published as a prebuilt archive and installed through the [TermuxVoid repository](https://github.com/termuxvoid/repo).

No Android Studio and no on-device compilation are required. Install the package, run `flutter doctor`, and start building.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Building Android apps](BUILDING_APPS.md)
- [Supported targets](#supported-targets)
- [Updating and uninstalling](#updating-and-uninstalling)
- [Build from source](#build-from-source)
- [Repository layout](#repository-layout)
- [Release process](#release-process)
- [TermuxVoid](#termuxvoid)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [Disclaimer](#disclaimer)

## Features

- **Prebuilt SDK** — no engine compilation on your device.
- **Termux-native** — patched Dart, Skia, and engine sources for the Termux environment.
- **Android, Linux, and web workflows** — build Android apps, run Linux desktop apps through Termux:X11, or serve a web build locally.
- **Hash-verified installs** — the TermuxVoid package checks the release archive SHA-256 before extracting.
- **Simple updates** — upgrade with the normal Termux package manager.
- **Scripted builds** — the same script and patches are used by the GitHub Actions release workflow.

## Requirements

| Requirement | Details |
| --- | --- |
| Device | Android device with `aarch64` (arm64) or `x86_64` userspace |
| Termux | Installed from [F-Droid](https://f-droid.org/packages/com.termux/) or [GitHub](https://github.com/termux/termux-app/releases) — not the Play Store build |
| Storage | About 2 GB free for the download, extraction, and package cache |
| Network | Internet access for the first install and for fetching dependencies |
| Optional | [Termux:X11](https://github.com/termux/termux-x11/releases) for Linux desktop apps |
| Optional | [`android-sdk`, `android-ndk`, and `android-cmake`](BUILDING_APPS.md) from TermuxVoid for Android builds |

> Release assets are built for `aarch64` and `x86_64`. The source build also accepts `arm` and `x86`, but those are not published as release assets.

## Installation

### 1. Add the TermuxVoid repository

Choose the repository that matches your Termux setup.

**APT (dpkg) Termux**

```bash
curl -fsSL https://github.com/termuxvoid/repo/raw/main/install.sh | bash
```

**Pacman Termux**

```bash
curl -fsSL https://github.com/termuxvoid/pacman-repo/raw/main/install-repo.sh | bash
```

> Prefer to inspect a script before running it? Download it from the [TermuxVoid APT repository](https://github.com/termuxvoid/repo) or [Pacman repository](https://github.com/termuxvoid/pacman-repo), read it, then run it locally.

### 2. Install Flutter

```bash
pkg update
pkg install flutter
```

The APT package declares `x11-repo` as a pre-dependency. Install `x11-repo` first if your Termux setup does not already include it. The package selects the release archive that matches your device architecture.

### 3. Verify

```bash
flutter --version
flutter doctor -v
```

`flutter doctor` may report missing Android tooling until you install and configure the Android packages. That is expected for Linux-only or web-only setups.

## Quick start

Create and run a project:

```bash
flutter create hello_termux
cd hello_termux
```

### Linux desktop

Install the Linux desktop build tools, start Termux:X11, point Flutter at its display, then run:

```bash
pkg install x11-repo termux-x11-nightly cmake ninja clang pkg-config gtk3
termux-x11 :0 >/dev/null 2>&1 &
export DISPLAY=:0
flutter run -d linux
```

### Android

Install the TermuxVoid Android packages, then connect a device:

```bash
pkg install android-sdk android-ndk android-cmake
flutter config --android-sdk "$PREFIX/opt/android-sdk"
flutter devices
flutter run -d <device-id>
```

`android-sdk` provides the SDK, platform tools, and build tools; `android-ndk` and `android-cmake` provide native compilation. No environment variables need to be exported.

Flutter projects also need the Termux-specific `local.properties`, `gradle.properties`, and `app/build.gradle.kts` values. See [Building Android apps](BUILDING_APPS.md) for the required edits, or use `apkgen-cli`, whose Flutter template already includes them.

### Web server

```bash
flutter run -d web-server --web-port 8080
```

Open `http://localhost:8080` in a browser on the device.

## Supported targets

| Target | Status | Notes |
| --- | --- | --- |
| Linux desktop (GTK) | Supported | Requires Termux:X11 |
| Android | Supported | Requires `android-sdk`, `android-ndk`, `android-cmake`, and a connected device |
| Web server | Supported | Use `flutter run -d web-server` |
| iOS / macOS / Windows | Not applicable | Requires their native toolchains |

## Updating and uninstalling

```bash
# Refresh package lists and upgrade Flutter
pkg update
pkg upgrade flutter

# Remove Flutter and its launcher
pkg uninstall flutter
```

The package installs the SDK to `$PREFIX/opt/flutter` and creates `$PREFIX/bin/flutter`. Uninstalling removes both.

## Build from source

The release workflow builds both `arm64` and `x64` on Linux x86_64 runners. A local Linux host works too; building inside Termux is not recommended because the engine build needs substantially more RAM and disk than most phones provide.

### Prerequisites

- Linux x86_64 host (or the GitHub Actions runner)
- Python 3
- Git and `curl`
- `ninja` and `dpkg-deb`
- Host build headers: `libfreetype-dev`, `libfontconfig-dev`
- [depot_tools](https://chromium.googlesource.com/chromium/tools/depot_tools.git) on `PATH` (`gclient`, `vpython3`)
- Android NDK **r27c**
- About 20 GB free disk space

### Build

```bash
git clone --depth 1 https://github.com/termuxvoid/flutter-termux.git
cd flutter-termux

git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$PWD/depot_tools:$PATH"

export ANDROID_NDK="$HOME/android-ndk-r27c"
python3 build.py --arch arm64   # or: --arch x64
```

`ANDROID_NDK` is only for building the Flutter SDK itself. Building apps uses `local.properties`; see [Building Android apps](BUILDING_APPS.md).

`build.py` reads the Flutter version from [`VERSION`](VERSION), clones that Flutter tag, syncs the engine dependencies, applies the patches in [`patches/`](patches), builds the debug engine, assembles the SDK, and writes:

```text
dist/flutter_<version>_aarch64.tar.gz
dist/flutter_<version>_x86_64.tar.gz
```

Useful options:

```bash
python3 build.py --help
python3 build.py --version 3.47.8 --arch arm64 --jobs 6
```

## Repository layout

```text
.
├── .github/workflows/release.yml   # Build and publish GitHub releases
├── build.py                        # Clone, patch, build, assemble, package
├── BUILDING_APPS.md                # Android app build setup on Termux
├── patches/
│   ├── engine.patch                # Termux engine and toolchain changes
│   ├── dart.patch                  # Dart host-platform detection
│   └── skia.patch                  # Skia Termux platform detection
├── VERSION                         # Flutter tag to build
└── README.md
```

## Release process

1. Update [`VERSION`](VERSION) to the new Flutter tag in a pull request.
2. Merge the pull request into `main`.
3. The [release workflow](.github/workflows/release.yml) checks whether the release already exists, builds both architectures in parallel on free `ubuntu-latest` runners, and publishes `flutter_<version>_aarch64.tar.gz` and `flutter_<version>_x86_64.tar.gz`.

The workflow only runs when `VERSION` changes on `main`. Pushing to a release branch or opening a pull request does not start it.

The build uses the upstream Flutter source plus the patches in this repository. Engine compilation is cached with ccache to keep later releases faster.

## TermuxVoid

This project is maintained as part of **TermuxVoid**, a third-party Termux repository for security, Android, AI, and utility tools.

| Resource | Link |
| --- | --- |
| TermuxVoid organization | [github.com/termuxvoid](https://github.com/termuxvoid) |
| This repository | [github.com/termuxvoid/flutter-termux](https://github.com/termuxvoid/flutter-termux) |
| APT repository | [github.com/termuxvoid/repo](https://github.com/termuxvoid/repo) |
| Pacman repository | [github.com/termuxvoid/pacman-repo](https://github.com/termuxvoid/pacman-repo) |
| Website | [termuxvoid.github.io](https://termuxvoid.github.io) |
| Flutter package page | [termuxvoid.github.io/tool.html?name=flutter](https://termuxvoid.github.io/tool.html?name=flutter) |
| Telegram | [t.me/termuxvoid](https://t.me/termuxvoid) |
| YouTube | [@alienkrishnorg](https://youtube.com/@alienkrishnorg) |

## Troubleshooting

### `flutter: command not found`

The TermuxVoid repository is probably not configured, or the package is not installed. Add the repository, run `pkg update`, then install `flutter` again. Open a new shell if `$PATH` was cached.

### `pkg install flutter` cannot find the package

Confirm that the TermuxVoid repository was added successfully. For APT, check `$PREFIX/etc/apt/sources.list.d/`; for Pacman, check the configured repository list. Re-run the installer if needed.

### Android toolchain errors in `flutter doctor`

Install `android-sdk`, `android-ndk`, and `android-cmake` from TermuxVoid and accept the Android licenses when prompted. A physical device or emulator must also be connected for `flutter run`.

### Linux desktop app does not start

Install the Termux:X11 app, start the server with `termux-x11 :0`, and export `DISPLAY=:0` before running `flutter run -d linux`.

### Installation fails with a checksum error

The download may be incomplete or corrupted. Clear the partial archive from `$TMPDIR` and retry:

```bash
rm -f "$TMPDIR/flutter.tar.gz"
pkg reinstall flutter
```

### Still stuck?

Open an issue with the command you ran, the full error output, and your device architecture (`uname -m`):

[github.com/termuxvoid/flutter-termux/issues](https://github.com/termuxvoid/flutter-termux/issues)

## Contributing

Pull requests are welcome. Please keep changes focused, test the build or packaging path when possible, and describe the Flutter version and device architecture used for testing.

For a release update, change `VERSION`, verify that all patches in `patches/` still apply, and open a pull request. Do not push release changes directly to `main`.

## Acknowledgments

- [mumumusuc/termux-flutter](https://github.com/mumumusuc/termux-flutter) — the original Flutter-on-Termux work.
- [yamsergey/yamsergey.termux.flutter](https://github.com/yamsergey/yamsergey.termux.flutter) — reference patches and build configuration.
- [Flutter](https://flutter.dev/) and [Dart](https://dart.dev/) — the upstream SDK and engine.
- [Termux](https://termux.dev/) — the Android terminal environment.
- [TermuxVoid](https://github.com/termuxvoid) — packaging, repository hosting, and release automation.

## Disclaimer

This is an unofficial community build. It is not affiliated with or endorsed by Google, the Flutter team, or the Termux project. Flutter and the Flutter logo are trademarks of Google LLC. Use at your own risk.

Flutter is distributed under the [BSD 3-Clause License](https://github.com/flutter/flutter/blob/master/LICENSE). See the upstream Dart, Skia, and Flutter repositories for their respective licenses.
