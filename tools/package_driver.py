#!/usr/bin/env python3
"""
package_driver.py - Validates and packages the PowerVR BXM-8-256 Mesa Vulkan driver
as the primary Adrenotools package (Eden / Azahar).
"""

import os
import sys
import json
import zipfile
import subprocess
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_DIR = os.path.join(REPO_ROOT, "research", "mesa-src", "build-android")
DRIVER_SO = os.path.join(BUILD_DIR, "src", "imagination", "vulkan", "libvulkan_powervr_mesa.so")
DIST_DIR = os.path.join(REPO_ROOT, "dist")

REQUIRED_EXPORTS = [
    "HMI",
    "vk_icdGetInstanceProcAddr",
    "vk_icdGetPhysicalDeviceProcAddr",
    "vk_icdNegotiateLoaderICDInterfaceVersion"
]

ALLOWED_SYSTEM_LIBS = {
    "libc.so",
    "libm.so",
    "libdl.so",
    "libz.so",
    "liblog.so",
    "libhardware.so",
    "libnativewindow.so",
    "libsync.so"
}


def find_cpp_runtime():
    """Locate the NDK libc++ runtime required by the C++ Mesa objects."""
    ndk = os.environ.get("ANDROID_NDK_ROOT") or os.environ.get("ANDROID_NDK_HOME")
    candidates = []
    if ndk:
        candidates.extend([
            os.path.join(ndk, "toolchains", "llvm", "prebuilt", "linux-x86_64",
                         "sysroot", "usr", "lib", "aarch64-linux-android",
                         "libc++_shared.so"),
            os.path.join(ndk, "sources", "cxx-stl", "llvm-libc++", "libs",
                         "arm64-v8a", "libc++_shared.so"),
        ])
    for path in candidates:
        if os.path.isfile(path):
            return path
    print("[-] libc++_shared.so not found in the configured Android NDK")
    sys.exit(1)

def check_binary():
    if not os.path.isfile(DRIVER_SO):
        print(f"[-] Driver binary not found: {DRIVER_SO}")
        sys.exit(1)

    print(f"[+] Found driver binary: {DRIVER_SO} ({os.path.getsize(DRIVER_SO):,} bytes)")

    # Verify exported symbols
    nm_tool = shutil.which("llvm-nm") or shutil.which("aarch64-linux-gnu-nm")
    readelf_tool = shutil.which("llvm-readelf") or shutil.which("aarch64-linux-gnu-readelf")
    if not nm_tool or not readelf_tool:
        print("[-] llvm-nm/llvm-readelf (or aarch64-linux-gnu equivalents) are required")
        sys.exit(1)
    nm_proc = subprocess.run(
        [nm_tool, "-D", DRIVER_SO],
        capture_output=True, text=True, check=True
    )
    exported_symbols = set()
    for line in nm_proc.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 3 and parts[1] in ("T", "D", "B", "R"):
            exported_symbols.add(parts[2])

    print("[*] Checking required exported symbols...")
    for sym in REQUIRED_EXPORTS:
        if sym in exported_symbols:
            print(f"  [OK] Exported: {sym}")
        else:
            print(f"  [FAIL] Missing required symbol: {sym}")
            sys.exit(1)

    # Verify DT_NEEDED
    readelf_proc = subprocess.run(
        [readelf_tool, "-d", DRIVER_SO],
        capture_output=True, text=True, check=True
    )
    needed = []
    for line in readelf_proc.stdout.splitlines():
        if "(NEEDED)" in line and "Shared library:" in line:
            lib = line.split("[")[1].split("]")[0]
            needed.append(lib)

    print("[*] Checking DT_NEEDED dynamic dependencies...")
    for lib in needed:
        if lib == "libc++_shared.so":
            print(f"  [OK] Bundled Android runtime dependency: {lib}")
        elif lib in ALLOWED_SYSTEM_LIBS:
            print(f"  [OK] System dependency: {lib}")
        else:
            print(f"  [FAIL] Disallowed or non-system dependency: {lib}")
            sys.exit(1)

def build_packages():
    os.makedirs(DIST_DIR, exist_ok=True)
    cpp_runtime = find_cpp_runtime()

    # Remove the retired secondary package if this is an incremental local build.
    old_icd_zip = os.path.join(DIST_DIR, "vulkan_pvr_bxm8256_icd.zip")
    if os.path.exists(old_icd_zip):
        os.remove(old_icd_zip)
    old_icd_dir = os.path.join(DIST_DIR, "standalone_icd")
    if os.path.isdir(old_icd_dir):
        shutil.rmtree(old_icd_dir)

    # Primary Adrenotools package (flat ZIP with meta.json and shared libraries).
    meta = {
        "schemaVersion": 1,
        "name": "PowerVR BXM-8-256 Mesa",
        "description": "Mesa vulkan_pvr driver for PowerVR B-Series BXM-8-256 (BVNC 35.3.408.101), Rogue DDK 1.15@6133110",
        "author": "Mesa / BXM Research",
        "packageVersion": "1",
        "vendor": "Imagination",
        "driverVersion": "Mesa 27.0.0-devel + MT6855 DDK 1.15",
        "minApi": 29,
        "libraryName": "libvulkan_powervr_mesa.so"
    }

    adrenotools_zip_path = os.path.join(DIST_DIR, "vulkan_pvr_bxm8256_adrenotools.zip")
    with zipfile.ZipFile(adrenotools_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps(meta, indent=2))
        z.write(DRIVER_SO, arcname="libvulkan_powervr_mesa.so")
        z.write(cpp_runtime, arcname="libc++_shared.so")

    print(f"[+] Created Adrenotools package: {adrenotools_zip_path} ({os.path.getsize(adrenotools_zip_path):,} bytes)")

if __name__ == "__main__":
    check_binary()
    build_packages()
