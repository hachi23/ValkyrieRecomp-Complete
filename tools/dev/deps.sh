#!/bin/bash
S="$(cd "$(dirname "$0")" && pwd)"; source "$S/env.sh"
# Copy every non-system dependency that resolves into /mingw64/bin.
ldd build-win/ValkyrieRecomp.exe | awk '/\/mingw64\/bin\//{print $3}' | sort -u | while read -r d; do
  cp -u "$d" build-win/ && echo "copied $(basename "$d")"
done
echo "--- unresolved ---"
ldd build-win/ValkyrieRecomp.exe | grep -i "not found" || echo none
