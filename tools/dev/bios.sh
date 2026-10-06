#!/bin/bash
set -uo pipefail
S="$(cd "$(dirname "$0")" && pwd)"; source "$S/env.sh"
cd psxrecomp
PSXRECOMP_BIOS_BUILD="$PWD/../build-recompiler" bash tools/regen_bios.sh --config bios/OpenBIOS.toml 2>&1 | tail -8
cd ..
bash "$S/build.sh"
grep -i "stale" "$S/build.log" | head -3
