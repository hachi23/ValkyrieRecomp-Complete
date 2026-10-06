#!/bin/bash
# Build emitters, verify both discs, then generate the game's C.
set -euo pipefail
source "$(dirname "$0")/env.sh"
bash psxrecomp/tools/ci/build_emitters.sh --jobs 16 2>&1 | tail -5
echo "=== verify Disc 1 ==="
python3 psxrecomp/psxrecomp_cli.py verify-disc --config game.toml --project-root . --disc "disc/Disc1/Valkyrie Profile (Undub) (Disc 1).cue" 2>&1 | tail -5 || true
echo "=== verify Disc 2 ==="
python3 psxrecomp/psxrecomp_cli.py verify-disc --config game.toml --project-root . --disc "disc/Disc2/Valkyrie Profile (Undub) (Disc 2).cue" 2>&1 | tail -5 || true
echo "=== generate ==="
python3 psxrecomp/psxrecomp_cli.py generate --config game.toml --project-root . --disc "disc/Disc1/Valkyrie Profile (Undub) (Disc 1).cue" 2>&1 | tail -25
ls generated | head -40
