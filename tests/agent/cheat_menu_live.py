#!/usr/bin/env python3
"""Drive the in-game cheat menu with real key events and check its effects.

Uses ydotool (kernel uinput) for keys and spectacle for window captures, so the
game window must be focused. settings.toml is restored afterwards.
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
SETTINGS = BUILD / 'settings.toml'
OUT = ROOT / 'analysis/agent/cheat-menu'
PORT = 4393
KEY = {'F5': 63, 'DOWN': 108, 'ENTER': 28, 'ESC': 1}


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


def press(name):
    code = KEY[name]
    subprocess.run(['ydotool', 'key', f'{code}:1', f'{code}:0'], check=True,
                   stdout=subprocess.DEVNULL)
    time.sleep(0.4)


def shot(name):
    subprocess.run(['spectacle', '-b', '-n', '-a', '-o', str(OUT / f'{name}.png')], check=True)
    time.sleep(0.5)


def selection():
    return {c['id']: c['selected'] for c in command('cheats_status')['cheats']}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original = SETTINGS.read_text()
    log = open(OUT / 'game.log', 'w')
    proc = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT)],
                            cwd=BUILD, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, 'PSX_BIOS_HLE': '0'})
    r = {}
    try:
        wait_until(lambda: command('ping'), 30, 'debug server did not answer')
        before = command('savestate_status')['generation']
        command('savestate', op='load', slot=3)
        wait_until(lambda: command('savestate_status')['generation'] != before, 30, 'load receipt missing')
        time.sleep(1.5)
        status = command('cheats_status')
        r['assist_before'] = status['assist']
        r['selection_before'] = selection()
        f0 = command('frame')['frame']
        t0 = time.monotonic()
        press('F5')
        shot('menu_open')
        press('ENTER')
        press('DOWN')
        press('DOWN')
        press('ENTER')
        shot('menu_toggled')
        r['settings_saved_while_open'] = SETTINGS.read_text()
        press('ESC')
        r['seconds_menu_open'] = round(time.monotonic() - t0, 1)
        r['frames_advanced_while_open'] = command('frame')['frame'] - f0
        status = command('cheats_status')
        r['assist_after'] = status['assist']
        r['selection_after'] = selection()
        f1 = command('frame')['frame']
        time.sleep(1.0)
        r['frames_advanced_after_close_1s'] = command('frame')['frame'] - f1
        shot('menu_closed')
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()
        SETTINGS.write_text(original)
    print(json.dumps(r, indent=2))


if __name__ == '__main__':
    main()
