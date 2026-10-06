#!/usr/bin/env python3
"""Check that the Skip Movies mod ends a movie, and only a movie.

Two scenes per run: the anime movie checkpoint (slot 10, a 24-bit MDEC movie)
sampled for 10 s, then the title menu's "Opening Movie" (slot 1), whose first
part is drawn live by the game, sampled for 60 s. Run 1 has the
valkyrie.skip-fmv feature off, run 2 on. mods/state.toml is restored afterwards.
Screenshots and the result land in analysis/agent/skip-fmv/.
"""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query

BUILD = Path(os.environ.get('BENCH_BUILD', ROOT / 'build-linux'))
STATE = BUILD / 'mods/state.toml'
# Slot 1 is the title menu, slot 10 the anime movie. Runs use a scratch copy.
SAVES = Path(os.environ.get('SKIP_FMV_SAVES', ROOT.parent / 'Valkyrie-recomp-perf/analysis/performance/fps-fix/state'))
OUT = ROOT / 'analysis/agent/skip-fmv'
PORT = 4397
NONE, DOWN, CROSS = 0xFFFF, 0xFFBF, 0xBFFF
START_HELD = '0xFFF7'
STATE_OFF = 'format_version = 2\n'
STATE_ON = """format_version = 2

[[package]]
id = "valkyrie.skip-fmv"
version = "1.0.0"

[[feature]]
package_id = "valkyrie.skip-fmv"
id = "skip-fmv"
enabled = true
"""


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


def route(*steps):
    command('input_route_clear')
    for frames, buttons in steps:
        command('input_route_append', frames=frames, buttons=buttons)
    command('input_route_start')
    wait_until(lambda: not command('input_route_status')['active'], 30, 'route did not finish')


def shot(name):
    kind = 'screenshot' if command('gpu_state').get('depth24') else 'screenshot_hires'
    try:
        command(kind, path=str(OUT / f'{name}.png'))
    except RuntimeError:
        command('screenshot', path=str(OUT / f'{name}.png'))


def load(slot):
    before = command('savestate_status')['generation']
    command('savestate', op='load', slot=slot)
    wait_until(lambda: command('savestate_status')['generation'] != before, 30, 'load receipt missing')


def sample(name, shots):
    base = command('fmv_state')['mdec_decode_count']
    start = time.monotonic()
    samples = []
    for at in shots:
        while time.monotonic() - start < at:
            f = command('fmv_state')
            samples.append({'t': round(time.monotonic() - start, 2), 'decodes': f['mdec_decode_count'] - base,
                            'depth24': command('gpu_state').get('depth24', 0), 'pad1': f['pad1']})
            time.sleep(0.25)
        shot(f'{name}_{at}s')
    movie = [s for s in samples if s['depth24']]
    return {'decodes': samples[-1]['decodes'],
            'last_depth24_s': movie[-1]['t'] if movie else 0.0,
            'depth24_at_end': samples[-1]['depth24'],
            'start_held_samples': sum(1 for s in samples if s['pad1'] == START_HELD),
            'auto_skip_fmv': command('fmv_state')['auto_skip_fmv']}


def movie_checkpoint(name):
    load(10)
    return sample(f'{name}_movie', (1, 3, 10))


def title_opening_movie(name):
    load(1)
    route((30, NONE), *[s for _ in range(4) for s in ((6, DOWN), (10, NONE))])
    time.sleep(0.5)
    shot(f'{name}_menu')
    route((6, CROSS), (10, NONE))
    return sample(f'{name}_title', (5, 20, 40, 60))


def run(name, state_text):
    STATE.write_text(state_text)
    saves = OUT / f'{name}.saves'
    shutil.rmtree(saves, ignore_errors=True)
    shutil.copytree(SAVES, saves)
    log = open(OUT / f'{name}.log', 'w')
    proc = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT),
                             '--memcard-dir', str(saves)], cwd=BUILD,
                            stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, 'PSX_BIOS_HLE': '0', 'DRI_PRIME': 'pci-0000_01_00_0!'})
    try:
        wait_until(lambda: command('ping'), 60, 'debug server did not answer')
        time.sleep(3)
        return {'movie_checkpoint': movie_checkpoint(name), 'title_opening_movie': title_opening_movie(name)}
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()
        shutil.rmtree(saves, ignore_errors=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original = STATE.read_text() if STATE.exists() else None
    result = {}
    try:
        result['skip_off'] = run('skip_off', STATE_OFF)
        result['skip_on'] = run('skip_on', STATE_ON)
    finally:
        if original is None:
            STATE.unlink(missing_ok=True)
        else:
            STATE.write_text(original)
    (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
