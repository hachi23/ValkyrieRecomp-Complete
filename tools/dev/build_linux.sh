#!/bin/bash
# Configure (if needed) and build the Linux ValkyrieRecomp into build-linux.
# Needs the generated game C (generated/, psxrecomp/generated/,
# psxrecomp/runtime/include/overlay_codegen_hash.h) like build.sh does.
# Debian/Ubuntu packages: see the "Install deps (Linux)" step in
# .github/workflows/release.yml, plus libcurl4-openssl-dev.
set -uo pipefail
S="$(cd "$(dirname "$0")" && pwd)"
cd "$S/../.."
export VULKAN_SDK="${VULKAN_SDK:-/usr}"
if [[ ! -f build-linux/build.ninja ]]; then
  cmake -S . -B build-linux -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON \
    -DPSX_ENABLE_VULKAN=ON -DGLSLC_EXE="$(command -v glslc)" \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    > "$S/configure-linux.log" 2>&1
  rc=$?
  grep -iE "vulkan|error|fingerprint|bios" "$S/configure-linux.log" | head -30
  [[ $rc -ne 0 ]] && { echo "CONFIGURE FAILED rc=$rc"; tail -40 "$S/configure-linux.log"; exit $rc; }
fi
cmake --build build-linux --target psx-runtime -j"$(nproc)" > "$S/build-linux.log" 2>&1
rc=$?
grep -E "error|FAILED" "$S/build-linux.log" | head -30
tail -3 "$S/build-linux.log"
echo "BUILD rc=$rc"
ls -la build-linux/ValkyrieRecomp 2>/dev/null
exit $rc
