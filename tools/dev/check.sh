#!/bin/bash
# Pre-commit check: build, runtime tests, generated-doc drift, launcher smoke.
# Run through PowerShell: & C:\msys64\usr\bin\bash.exe -l tools/dev/check.sh
set -uo pipefail
S="$(cd "$(dirname "$0")" && pwd)"; source "$S/env.sh"
failed=()

echo "== build"
"$S/build.sh" > "$S/check-build.out" 2>&1 || failed+=("build (see tools/dev/build.log)")
grep "BUILD rc" "$S/check-build.out"

echo "== runtime tests"
pass=0
for t in psxrecomp/runtime/tests/*.py; do
  if python "$t" > "$S/check-test.out" 2>&1; then
    pass=$((pass + 1))
  else
    echo "FAIL $(basename "$t")"; tail -5 "$S/check-test.out"
    failed+=("test $(basename "$t")")
  fi
done
echo "$pass passed"

echo "== debug command docs"
(cd psxrecomp && python tools/gen_tcp_commands.py --check) || failed+=("docs/TCP_COMMANDS.md is stale")

echo "== launcher smoke"
shot="$S/check-launcher.png"
rm -f "$shot"
win_shot="$(cygpath -w "$shot")"
(cd build-win && LNG_UI_SCALE=100 LNG_SCRIPT="wait:60;view:settings;wait:15;shot:$win_shot;quit" \
  timeout 60 ./ValkyrieRecomp.exe --launcher > "$S/check-launcher.out" 2>&1)
if [[ -s "$shot" ]]; then echo "launcher drew $shot"; else failed+=("launcher smoke (no screenshot)"); fi

rm -f "$S/check-build.out" "$S/check-test.out"
if (( ${#failed[@]} )); then
  echo; echo "CHECK FAILED:"; printf '  %s\n' "${failed[@]}"; exit 1
fi
echo; echo "CHECK OK"
