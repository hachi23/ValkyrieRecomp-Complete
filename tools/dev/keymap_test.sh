#!/usr/bin/env bash
# Build and run psxrecomp/runtime/tests/test_host_keymap.c against the SDL3
# that build-win fetched. Optional $1: a different host_keymap.c to test.
source "$(dirname "$0")/env.sh"
set -e
RT=psxrecomp/runtime
SDL=build-win/_deps
SRC=${1:-$RT/src/host_keymap.c}
OUT=build-win/host_keymap_test.exe
gcc -std=c11 -O1 -DSDL_MAIN_HANDLED -DPSX_SDL3=1 \
    -I"$RT/include" -I"$SDL/sdl3-src/include" -I"$SDL/sdl3-build/include-config-release" \
    "$RT/tests/test_host_keymap.c" "$SRC" "$SDL/sdl3-build/libSDL3.a" \
    -lsetupapi -lwinmm -limm32 -lversion -lole32 -loleaut32 -luuid -lgdi32 \
    -luser32 -lshell32 -ladvapi32 -lcfgmgr32 -o "$OUT"
cd build-win && ./host_keymap_test.exe
