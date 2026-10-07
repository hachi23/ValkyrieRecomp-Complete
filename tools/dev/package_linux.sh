#!/bin/bash
# Pack build-linux into a ready-to-play folder and tarball.
# Personal use only: this copies YOUR disc images and saves into the package.
# Never share or upload its output. Public releases go through
# scripts/package_setup_release.sh, which contains no game data.
# package_linux.sh <discs folder with "Disc 1" and "Disc 2"> <saves folder> <out dir>
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd)"
ROOT="$S/../.."
DISCS="$1"; SAVES="$2"; OUT="$3"
PKG="$OUT/ValkyrieRecomp-Linux"
B="$ROOT/build-linux"
rm -rf "$PKG"; mkdir -p "$PKG/disc/Disc1" "$PKG/disc/Disc2" "$PKG/logs"
cp "$B/ValkyrieRecomp" "$PKG/"
cp -r "$B/assets" "$B/bios" "$B/cheats" "$B/mods" "$PKG/"
cp "$B/game.toml" "$B/game_options.toml" "$B/psx_game_version.txt" \
   "$B/psx_mod_catalog_psx-runtime.txt" "$B/psxrecomp_exe_name-psx-runtime.txt" \
   "$B/psxrecomp_overlay_flavor-psx-runtime.txt" "$PKG/"
cp "$DISCS/Disc 1/"*.cue "$DISCS/Disc 1/"*.bin "$PKG/disc/Disc1/"
cp "$DISCS/Disc 2/"*.cue "$DISCS/Disc 2/"*.bin "$PKG/disc/Disc2/"
cp -r "$SAVES" "$PKG/saves"
cp "$S/linux/play.sh" "$S/linux/HOW_TO_PLAY.md" "$PKG/"
chmod +x "$PKG/ValkyrieRecomp" "$PKG/play.sh"
tar -C "$OUT" -cf "$OUT/ValkyrieRecomp-Linux.tar" ValkyrieRecomp-Linux
ls -la "$OUT/ValkyrieRecomp-Linux.tar"
