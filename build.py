#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
from pathlib import Path

FLUTTER_REPO = "https://github.com/flutter/flutter.git"
VERSION_FILE = Path(__file__).resolve().parent / "VERSION"
GCLIENT = """solutions = [
  {
    "managed": False,
    "name": ".",
    "url": "https://github.com/flutter/flutter",
    "deps_file": "DEPS",
    "safesync_url": "",
    "custom_deps": {
      "engine/src/fuchsia/sdk/linux": None,
      "engine/src/third_party/google_fonts_for_unit_tests": None,
      "engine/src/flutter/third_party/java/openjdk": None,
    },
    "custom_vars": {
      "setup_githooks": False,
      "use_cipd_goma": False,
      "download_emsdk": False,
      "download_dart_sdk": False,
      "download_linux_deps": False,
      "download_fuchsia_sdk": False,
      "download_android_deps": False,
      "download_windows_deps": False,
      "download_fuchsia_deps": False,
    },
  },
]
"""

ARCHES = {"arm64": "aarch64", "arm": "arm", "x64": "x86_64", "x86": "i686"}
MODE = "debug"
NDK_HOST = "linux-x86_64"
API = 26

# system libraries the engine is linked against; headers and .so files
# are unpacked from the Termux repos into a fake sysroot.
SYSROOT_REPOS = [
    ("https://packages-cf.termux.dev/apt/termux-main/", "stable", {
        "at-spi2-core", "brotli", "dbus", "fontconfig", "freetype", "fribidi",
        "gdk-pixbuf", "glib", "harfbuzz", "libcairo", "libepoxy", "libexpat",
        "libffi", "libglvnd", "libglvnd-dev", "libgraphite", "libjpeg-turbo",
        "liblzma", "libpixman", "libpng", "libtiff", "libwayland", "libx11",
        "libxau", "libxcb", "libxcursor", "libxdmcp", "libxext", "libxfixes",
        "libxft", "libxi", "libxrandr", "libxrender", "libxtst", "pango",
        "pcre2", "swiftshader", "xorgproto", "zlib", "zstd",
    }),
    ("https://packages-cf.termux.dev/apt/termux-x11/", "x11", {
        "gtk3", "libxcomposite", "libxdamage", "libxinerama", "libxkbcommon",
    }),
]

ARTIFACTS = [
    "flutter_tester",
    "font-subset",
    "icudtl.dat",
    "impellerc",
    "gen_snapshot",
    "libpath_ops.so",
    "libtessellator.so",
    "gen/frontend_server_aot.dart.snapshot",
    "gen/const_finder.dart.snapshot",
    "gen/flutter/lib/snapshot/isolate_snapshot.bin",
    "gen/flutter/lib/snapshot/vm_isolate_snapshot.bin",
]

STAMPS = ["engine-dart-sdk", "flutter_sdk", "font-subset", "linux-sdk"]

# Not used by the flutter command at runtime; .git stays because flutter exits
# without it.
EXCLUDED = [".agents", ".github", ".idea", ".vscode", "dev", "docs",
            "engine", "examples"]


def fail(message):
    raise SystemExit(f"error: {message}")


def read_version():
    if not VERSION_FILE.is_file():
        fail(f"missing {VERSION_FILE.name}")
    version = VERSION_FILE.read_text().strip()
    if not version:
        fail(f"empty {VERSION_FILE.name}")
    return version


def run(command, cwd=None, env=None):
    print("+", " ".join(str(x) for x in command), flush=True)
    subprocess.run([str(x) for x in command], cwd=cwd, env=env, check=True)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["curl", "-fL", "--retry", "3", "--retry-delay", "2", "-o", dest, url])


def fetch(url):
    result = subprocess.run(
        ["curl", "-fsSL", "--retry", "3", url],
        check=True, text=True, capture_output=True)
    return result.stdout


def need(path):
    path = Path(path)
    if not path.exists():
        fail(f"missing build output: {path}")
    return path


def copy(src, dst):
    src, dst = Path(src), Path(dst)
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def clone(flutter, version):
    if flutter.exists():
        shutil.rmtree(flutter)
    run([
        "git", "clone", "--depth", "1", "--branch", version,
        FLUTTER_REPO, flutter,
    ], env=os.environ | {"GIT_TERMINAL_PROMPT": "0"})


def sync(flutter):
    (flutter / ".gclient").write_text(GCLIENT)
    run(
        ["gclient", "sync", "-DR", "--no-history"],
        cwd=flutter,
        env=os.environ | {"GIT_TERMINAL_PROMPT": "0"})


def apply_patches(flutter, patches):
    run(["git", "apply", patches / "engine.patch"], cwd=flutter)
    run(
        ["git", "apply", patches / "dart.patch"],
        cwd=flutter / "engine/src/flutter/third_party/dart")
    run(
        ["git", "apply", patches / "skia.patch"],
        cwd=flutter / "engine/src/flutter/third_party/skia")


def resolve_packages(repo, dist, arch, wanted):
    url = urllib.parse.urljoin(
        repo, f"dists/{dist}/main/binary-{arch}/Packages")
    found = {}
    current = None
    for line in fetch(url).splitlines():
        if line.startswith("Package: "):
            current = line[9:].strip()
        elif current in wanted and line.startswith("Filename: "):
            found[current] = urllib.parse.urljoin(repo, line[10:].strip())
    missing = wanted - found.keys()
    if missing:
        fail(f"packages not found: {', '.join(sorted(missing))}")
    return found


def make_sysroot(work, arch):
    root = work / "sysroot"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with tempfile.TemporaryDirectory(dir=work) as tmp:
        for repo, dist, wanted in SYSROOT_REPOS:
            for url in resolve_packages(repo, dist, arch, wanted).values():
                deb = Path(tmp) / url.rsplit("/", 1)[-1]
                download(url, deb)
                run(["dpkg-deb", "-x", deb, root])

    termux = root / "data/data/com.termux/files/usr"
    if not (termux / "include").is_dir():
        fail("sysroot extraction failed")
    (root / "usr").symlink_to("data/data/com.termux/files/usr")
    (termux / "lib/libpthread.a").write_text("INPUT(-lc)\n")
    return root


def out_dir(flutter, arch):
    return flutter / "engine/src/out" / f"linux_{MODE}_{arch}"


def configure(flutter, ndk, arch, sysroot):
    toolchain = ndk / "toolchains/llvm/prebuilt" / NDK_HOST
    if not toolchain.is_dir():
        fail(f"NDK toolchain not found: {toolchain}")
    termux_host = (
        os.environ.get("PREFIX") == "/data/data/com.termux/files/usr")

    command = [
        "vpython3", "engine/src/flutter/tools/gn",
        "--linux",
        "--linux-cpu", arch,
        "--enable-fontconfig",
        "--no-goma",
        "--no-backtrace",
        "--clang",
        "--lto",
        "--no-enable-unittests",
        "--no-build-embedder-examples",
        "--no-prebuilt-dart-sdk",
        "--target-toolchain", toolchain,
        "--runtime-mode", MODE,
        "--no-build-glfw-shell",
        "--gn-args", "symbol_level=0",
        "--gn-args", "arm_use_neon=false",
        "--gn-args", "arm_optionally_use_neon=true",
        "--gn-args", "dart_include_wasm_opt=false",
        "--gn-args", "dart_platform_sdk=false",
        "--gn-args", "is_desktop_linux=false",
        "--gn-args", "use_default_linux_sysroot=false",
        "--gn-args", "dart_support_perfetto=false",
        "--gn-args", "skia_use_perfetto=false",
        "--gn-args", f'custom_sysroot="{sysroot}"',
        "--gn-args", "is_termux=true",
        "--gn-args", f"is_termux_host={str(termux_host).lower()}",
        "--gn-args", f"termux_api_level={API}",
        "--gn-args", 'extra_ldflags=["-lEGL", "-lGLESv2"]',
    ]
    run(command, cwd=flutter)


def build(flutter, arch, jobs):
    command = ["ninja", "-C", out_dir(flutter, arch), "-k", "0"]
    if jobs:
        command.append(f"-j{jobs}")
    command.append("flutter")
    run(command)


def assemble(flutter, arch):
    out = out_dir(flutter, arch)
    cache = flutter / "bin/cache"
    shutil.rmtree(cache, ignore_errors=True)
    cache.mkdir(parents=True)

    copy(need(out / "dart-sdk"), cache / "dart-sdk")
    copy(need(out / "gen/dart-pkg/sky_engine"), cache / "pkg/sky_engine")
    copy(
        need(flutter / "engine/src/flutter/lib/gpu"),
        cache / "pkg/flutter_gpu")

    engine = cache / "artifacts/engine" / f"linux-{arch}"
    engine.mkdir(parents=True)
    copy(
        need(flutter / "engine/src/flutter/impeller/compiler/shader_lib"),
        engine / "shader_lib")
    for name in ARTIFACTS:
        copy(need(out / name), engine / Path(name).name)

    for name in ["flutter_linux", "libflutter_linux_gtk.so"]:
        if (out / name).exists():
            copy(out / name, engine / name)

    # Keep the cache from fetching glibc engine artifacts on linux desktop commands.
    for mode in ["profile", "release"]:
        (engine.parent / f"linux-{arch}-{mode}").mkdir(exist_ok=True)

    common = cache / "artifacts/engine/common"
    patched = out / "flutter_patched_sdk"
    for name in ["platform_strong.dill", "vm_outline_strong.dill"]:
        copy(need(patched / name), common / "flutter_patched_sdk" / name)
    if (out / "flutter_patched_sdk_product").is_dir():
        copy(
            out / "flutter_patched_sdk_product",
            common / "flutter_patched_sdk_product")

    version = (flutter / "bin/internal/engine.version").read_text().strip()
    if not version:
        fail("empty engine version")
    for stamp in STAMPS:
        (cache / f"{stamp}.stamp").write_text(version)

    need(cache / "dart-sdk/bin/dart")
    need(engine / "gen_snapshot")


def package_tar(flutter, output, arch):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    result = subprocess.run(
        ["git", "-C", flutter, "ls-files", "-z"],
        check=True, capture_output=True)
    tracked = [
        os.fsdecode(name) for name in result.stdout.split(b"\0") if name
    ]

    with tarfile.open(
            output, "w:gz", compresslevel=9, format=tarfile.PAX_FORMAT) as tar:
        for name in tracked:
            if name.split("/", 1)[0] in EXCLUDED:
                continue
            path = flutter / name
            if not path.exists():
                fail(f"tracked file missing: {name}")
            tar.add(path, arcname=f"flutter/{name}", recursive=False)
        tar.add(flutter / ".git", arcname="flutter/.git")
        tar.add(flutter / "bin/cache", arcname="flutter/bin/cache")
        if (flutter / "version").exists():
            tar.add(flutter / "version", arcname="flutter/version")

    with tarfile.open(output, "r:gz") as tar:
        names = tar.getnames()

    required = [
        "flutter/.git/HEAD",
        "flutter/bin/internal/engine.version",
        "flutter/bin/cache/dart-sdk/bin/dart",
        f"flutter/bin/cache/artifacts/engine/linux-{arch}/gen_snapshot",
        "flutter/version",
    ]
    missing = [name for name in required if name not in names]
    if missing:
        fail(f"archive is incomplete: {', '.join(missing)}")

    size = output.stat().st_size / 1024 / 1024
    print(f"created {output} ({size:.1f} MiB)", flush=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build Flutter for Termux and package it as tar.gz")
    parser.add_argument(
        "--version", default=None,
        help="Flutter tag (default: the VERSION file)")
    parser.add_argument("--arch", default="arm64", choices=ARCHES)
    parser.add_argument("--jobs", type=int, default=os.cpu_count())
    parser.add_argument("--work-dir", default=".work")
    parser.add_argument("--output-dir", default="dist")
    parser.add_argument("--patches", default="patches")
    return parser.parse_args()


def main():
    args = parse_args()
    version = args.version or read_version()
    ndk = os.environ.get("ANDROID_NDK") or os.environ.get("ANDROID_NDK_HOME")
    if not ndk:
        fail("ANDROID_NDK is not set")

    patches = Path(args.patches).resolve()
    for name in ["engine.patch", "dart.patch", "skia.patch"]:
        if not (patches / name).is_file():
            fail(f"missing patch: {patches / name}")

    work = Path(args.work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    flutter = work / "flutter"
    arch = ARCHES[args.arch]

    clone(flutter, version)
    sync(flutter)
    apply_patches(flutter, patches)

    sysroot = make_sysroot(work, arch)
    configure(flutter, Path(ndk), args.arch, sysroot)
    build(flutter, args.arch, args.jobs)

    assemble(flutter, args.arch)
    run(["git", "reset", "--hard"], cwd=flutter)
    run(["git", "sparse-checkout", "init", "--no-cone"], cwd=flutter)
    run(
        ["git", "sparse-checkout", "set", "/*"]
        + [f"!/{name}/" for name in EXCLUDED],
        cwd=flutter)
    (flutter / "version").write_text(f"{version}\n")

    output = (
        Path(args.output_dir).resolve()
        / f"flutter_{version}_{arch}.tar.gz")
    package_tar(flutter, output, args.arch)


if __name__ == "__main__":
    main()
