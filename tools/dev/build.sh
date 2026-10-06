#!/bin/bash
# Configure (if needed) and build ValkyrieRecomp into build-win.
set -uo pipefail
S="$(cd "$(dirname "$0")" && pwd)"; source "$S/env.sh"
if [[ ! -f build-win/build.ninja ]]; then
  cmake -S . -B build-win -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON -DPSX_ENABLE_VULKAN=ON \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache > "$S/configure.log" 2>&1
  rc=$?
  grep -iE "vulkan|error|warning: .*fingerprint|bios|overlays_static" "$S/configure.log" | head -30
  [[ $rc -ne 0 ]] && { echo "CONFIGURE FAILED rc=$rc"; tail -40 "$S/configure.log"; exit $rc; }
fi
cmake --build build-win --target psx-runtime -j16 > "$S/build.log" 2>&1
rc=$?
grep -E "error|FAILED" "$S/build.log" | head -30
tail -3 "$S/build.log"
echo "BUILD rc=$rc"
ls -la build-win/*.exe 2>/dev/null
exit $rc
