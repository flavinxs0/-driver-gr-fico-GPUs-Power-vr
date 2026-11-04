#!/usr/bin/env bash
#
# setup_mesa.sh (VERSION CORREGIDA)
# Clona Mesa y aplica los 5 parches BXM-8-256.
#
# El script original usaba como base el commit fa7228e1a8ae ("Mesa 25.0.0"), pero los
# parches estan fechados el 23-24 de octubre de 2026 y el 0005 modifica
# pvr_arch_cmd_buffer.c, un archivo que no existe en Mesa 25.0. Con esa base los parches
# no aplican. Aqui se prueban commits de la rama principal de Mesa con fechas
# decrecientes hasta que los 5 parches apliquen limpiamente.
#
# Para forzar una base concreta:  MESA_BASE_COMMIT=<sha> ./tools/setup_mesa.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MESA_DIR="${ROOT_DIR}/research/mesa-src"
PATCHES_DIR="${ROOT_DIR}/patches"
MESA_URL="${MESA_URL:-https://gitlab.freedesktop.org/mesa/mesa.git}"

if [ -d "${MESA_DIR}/.git" ] && git -C "${MESA_DIR}" rev-parse --verify -q bxm-ddk25-offline >/dev/null; then
    echo "[+] Mesa ya preparado en ${MESA_DIR} (rama bxm-ddk25-offline)"
    exit 0
fi

rmdir "${MESA_DIR}" 2>/dev/null || true
echo "[*] Clonando Mesa (clon parcial, tarda unos minutos)..."
git clone --filter=blob:none "${MESA_URL}" "${MESA_DIR}"
cd "${MESA_DIR}"
git config user.name  "bxm-build"
git config user.email "bxm-build@example.invalid"

DEFAULT_REF="$(git symbolic-ref --short refs/remotes/origin/HEAD)"

try_base() {
    local base="$1" label="$2"
    echo "[*] Probando base ${base:0:12} (${label})..."
    git checkout -q -B bxm-ddk25-offline "${base}"
    if git am --3way -q "${PATCHES_DIR}"/*.patch >/tmp/git-am.log 2>&1; then
        echo "[+] Los 5 parches aplicaron sobre ${base}"
        echo "${base}" > "${ROOT_DIR}/BASE_COMMIT.txt"
        return 0
    fi
    echo "    No aplican: $(grep -m1 -iE 'error|conflict|patch failed' /tmp/git-am.log || echo 'ver /tmp/git-am.log')"
    git am --abort >/dev/null 2>&1 || true
    return 1
}

if [ -n "${MESA_BASE_COMMIT:-}" ]; then
    try_base "${MESA_BASE_COMMIT}" "forzado por MESA_BASE_COMMIT" && exit 0
    echo "[-] Los parches no aplican sobre MESA_BASE_COMMIT=${MESA_BASE_COMMIT}"; exit 1
fi

# El primer parche es del 23-oct-2026 18:48 +0530 (13:18 UTC): la base es anterior o igual.
CANDIDATES=("2026-10-23 13:00" "2026-10-22 23:59" "2026-10-21 23:59" "2026-10-20 23:59"
            "2026-10-19 23:59" "2026-10-18 23:59" "2026-10-16 23:59" "2026-10-14 23:59"
            "2026-10-12 23:59" "2026-10-10 23:59" "2026-10-07 23:59" "2026-10-04 23:59"
            "2026-10-01 23:59" "2026-09-25 23:59" "2026-09-15 23:59")

for when in "${CANDIDATES[@]}"; do
    base="$(git rev-list -1 --before="${when} +0000" "${DEFAULT_REF}" || true)"
    [ -n "${base}" ] || continue
    try_base "${base}" "${when} UTC" && exit 0
done

echo "[-] Ningun commit candidato admite los parches. Abre /tmp/git-am.log y mandame el contenido."
exit 1
