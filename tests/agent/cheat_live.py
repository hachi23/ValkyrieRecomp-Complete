#!/usr/bin/env python3
"""Prove the cheat engine writes guest RAM only while its gates allow it.

Launches the game, restores the first_field checkpoint, then drives the
battle-item-use cheat (D005A7BC FFFF / 8005A7BC 0000) through the debug server:
seed the trigger value, wait a few frames, read it back.
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

PORT = 4392
ADDR = 0x8005A7BC
CHEAT = 'battle-item-use'


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


def seed_and_read():
    for i, byte in enumerate((0xFF, 0xFF)):
        command('write_ram', addr=f'{ADDR + i:08X}', val=f'{byte:02X}')
    start = command('frame')['frame']
    wait_until(lambda: command('frame')['frame'] >= start + 3, 5, 'frames did not advance')
    raw = bytes.fromhex(command('read_ram', addr=f'{ADDR:08X}', len=2)['hex'])
    return raw[0] | raw[1] << 8


def main():
    out = ROOT / 'analysis/agent/cheat-live.log'
    log = open(out, 'w')
    proc = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT)],
                            cwd=ROOT / 'build-linux', stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, 'PSX_BIOS_HLE': '0'})
    results = {}
    try:
        wait_until(lambda: command('ping'), 30, 'debug server did not answer')
        before = command('savestate_status')['generation']
        command('savestate', op='load', slot=3)
        wait_until(lambda: command('savestate_status')['generation'] != before, 30, 'load receipt missing')
        status = command('cheats_status')
        results['catalog_loaded'] = status['loaded']
        results['catalog_ids'] = [c['id'] for c in status['cheats']]
        command('cheats_assist', enabled=0)
        command('cheats_set', cheat=CHEAT, enabled=1)
        results['assist_off_selected'] = seed_and_read()
        command('cheats_assist', enabled=1)
        results['assist_on_selected'] = seed_and_read()
        command('cheats_set', cheat=CHEAT, enabled=0)
        results['assist_on_deselected'] = seed_and_read()
        results['unknown_cheat_rejected'] = query('127.0.0.1', PORT, {
            'cmd': 'cheats_set', 'cheat': 'no-such-cheat', 'enabled': 1}).get('ok') is False
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()
    expected = {'assist_off_selected': 0xFFFF, 'assist_on_selected': 0x0000,
                'assist_on_deselected': 0xFFFF}
    results['pass'] = (results['catalog_loaded'] and results['unknown_cheat_rejected']
                       and all(results[k] == v for k, v in expected.items()))
    print(json.dumps(results, indent=2))
    sys.exit(0 if results['pass'] else 1)


if __name__ == '__main__':
    main()
