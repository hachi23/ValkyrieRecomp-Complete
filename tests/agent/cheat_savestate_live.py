#!/usr/bin/env python3
"""Check that save states record active cheats and warn on a mismatched load.

Restores first_field, turns on battle-item-use, saves to scratch slot 11, turns
the cheat off, and loads slot 11 again. The warning toast is checked from a
window capture. Slot 11 files created here are removed afterwards.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query

BUILD = ROOT / 'build-linux'
SAVES = ROOT / 'saves'
OUT = ROOT / 'analysis/agent/cheat-savestate'
PORT = 4394
SLOT = 11


def command(cmd, **kw):
    response = query('127.0.0.1', PORT, {'cmd': cmd, **kw})
    if not isinstance(response, dict) or response.get('ok') is not True:
        raise RuntimeError(f'{cmd} failed: {response}')
    return response


def wait_until(predicate, timeout, what):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except OSError:
            pass
        time.sleep(0.2)
    raise TimeoutError(what)


def run_op(op, slot):
    before = command('savestate_status')['generation']
    command('savestate', op=op, slot=slot)
    wait_until(lambda: command('savestate_status')['generation'] != before, 30, f'{op} receipt missing')
    status = command('savestate_status')
    assert status['last_ok'] == 1 and status['last_op'] == op, status


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scratch = sorted(SAVES.glob(f'*/state_*_slot{SLOT:02d}.*'))
    if scratch:
        raise SystemExit(f'slot {SLOT} already has files: {scratch}')
    log = open(OUT / 'game.log', 'w')
    proc = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT)],
                            cwd=BUILD, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, 'PSX_BIOS_HLE': '0'})
    r = {}
    try:
        wait_until(lambda: command('ping'), 30, 'debug server did not answer')
        run_op('load', 3)
        command('cheats_assist', enabled=1)
        command('cheats_set', cheat='battle-item-use', enabled=1)
        run_op('save', SLOT)
        sidecar = next(SAVES.glob(f'*/state_*_slot{SLOT:02d}.cheats'))
        r['sidecar'] = sidecar.read_text()
        run_op('load', SLOT)
        time.sleep(0.5)
        subprocess.run(['spectacle', '-b', '-n', '-a', '-o', str(OUT / 'same_cheats.png')], check=True)
        command('cheats_set', cheat='battle-item-use', enabled=0)
        time.sleep(3.5)
        run_op('load', SLOT)
        time.sleep(0.5)
        subprocess.run(['spectacle', '-b', '-n', '-a', '-o', str(OUT / 'different_cheats.png')], check=True)
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()
        for f in SAVES.glob(f'*/state_*_slot{SLOT:02d}.*'):
            f.unlink()
    print(json.dumps(r, indent=2))


if __name__ == '__main__':
    main()
