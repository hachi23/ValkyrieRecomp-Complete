#!/usr/bin/env bash
# Build the Linux setup-host release zip locally, the same way release.yml
# does on GitHub, without spending Actions minutes.
#
# Works in a fresh clone of the committed HEAD (submodules at their pinned,
# pushed commits), so this checkout's generated/, saves and build dirs are
# never touched.
#
# Usage: scripts/local_release.sh [version] [work-dir]
# Writes: dist/ValkyrieRecomp-<version>-linux-x64.zip in this checkout.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-$(tr -d '[:space:]' <"${ROOT}/VERSION")}"
VERSION="${VERSION#v}"
WORK="${2:-${TMPDIR:-/tmp}/valkyrie-release}"
JOBS="$(nproc)"

if [[ -n "$(git -C "${ROOT}" status --porcelain --untracked-files=no)" ]]; then
  echo "warning: uncommitted changes are not part of the release" >&2
fi

rm -rf "${WORK}"
git clone --quiet "${ROOT}" "${WORK}"
git -C "${WORK}" remote set-url origin "$(git -C "${ROOT}" remote get-url origin)"
git -C "${WORK}" submodule update --init --recursive --quiet

cd "${WORK}"
printf '%s\n' "${VERSION}" >VERSION
bash psxrecomp/tools/ci/record_pins.sh
bash psxrecomp/tools/ci/clear_generated.sh
bash psxrecomp/tools/ci/build_emitters.sh --framework psxrecomp \
  --build-dir build-recompiler --jobs "${JOBS}"

cmake -S . -B build-ci -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DPSXRECOMP_FORCE_SETUP_HOST=ON \
  -DPSXRECOMP_ALLOW_NO_BIOS=ON \
  -DPSX_SETUP_WIZARD=ON \
  -DPSX_GAME_VERSION="${VERSION}" \
  -DGLSLC_EXE="$(command -v glslc)" \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  | tee build-ci-configure.log
grep -q 'Vulkan backend: headers' build-ci-configure.log ||
  { echo "error: Vulkan backend not enabled" >&2; exit 1; }
cmake --build build-ci --target psx-runtime -j"${JOBS}"

STAMP="$(find build-ci -name psx_game_version.txt -type f | head -n1)"
BUILT="$(tr -d '[:space:]' <"${STAMP}")"
[[ "${BUILT#v}" == "${VERSION}" ]] ||
  { echo "error: version stamp ${BUILT} != ${VERSION}" >&2; exit 1; }

find build-recompiler -type f \( -name psxrecomp-bios -o -name psxrecomp-game \) -exec chmod +x {} +
RELEASE_VERSION="${VERSION}" bash scripts/package_setup_release.sh build-ci linux-x64 build-recompiler

mkdir -p "${ROOT}/dist"
cp dist/ValkyrieRecomp-*-linux-x64.zip "${ROOT}/dist/"
ls -la "${ROOT}"/dist/ValkyrieRecomp-*-linux-x64.zip
