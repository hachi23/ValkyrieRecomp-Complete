#!/usr/bin/env python3
"""Launch the game once per graphics setting, restore a checkpoint, capture.

Writes [video] keys into build-linux/settings.toml for each run and restores the
original file afterwards. Captures land under analysis/agent/graphics-<stamp>/.
"""
import json
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query

BUILD = ROOT / 'build-linux'
SETTINGS = BUILD / 'settings.toml'
PORT = 4391
SLOT = 3

RUNS = {
    'scale1_nearest_smooth': dict(supersampling=1, texture_filtering='nearest', antialiasing=True),
    'scale2_nearest_smooth': dict(supersampling=2, texture_filtering='nearest', antialiasing=True),
    'scale4_nearest_smooth': dict(supersampling=4, texture_filtering='nearest', antialiasing=True),
    'scale1_bilinear_smooth': dict(supersampling=1, texture_filtering='bilinear', antialiasing=True),
    'scale1_nearest_sharp': dict(supersampling=1, texture_filtering='nearest', antialiasing=False),
}


def toml_value(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        return str(v)
    return json.dumps(v)


def settings_with(original, video):
    if '[video]' in original:
        raise SystemExit('settings.toml already has [video]; move it aside before running')
    block = ['[video]', 'renderer = "vulkan"', 'window_width = 960', 'fullscreen = 0']
    block += [f'{k} = {toml_value(v)}' for k, v in video.items()]
    return '\n'.join(block) + '\n\n' + original


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


def command(cmd, **kw):
    response = query('127.0.0.1', PORT, {'cmd': cmd, **kw})
    if not isinstance(response, dict) or response.get('ok') is not True:
        raise RuntimeError(f'{cmd} failed: {response}')
    return response


def capture(name, video, out):
    log = open(out / f'{name}.log', 'w')
    env = {**os.environ, 'PSX_BIOS_HLE': '0'}
    proc = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT)],
                            cwd=BUILD, stdout=log, stderr=subprocess.STDOUT, env=env)
    try:
        wait_until(lambda: command('ping'), 30, 'debug server did not answer')
        before = command('savestate_status')['generation']
        command('savestate', op='load', slot=SLOT)
        wait_until(lambda: command('savestate_status')['generation'] != before, 30, 'load receipt missing')
        status = command('savestate_status')
        assert status['last_ok'] == 1 and status['last_op'] == 'load', status
        time.sleep(2)
        hires = command('screenshot_hires', path=str(out / f'{name}.hires.png'))
        subprocess.run(['spectacle', '-b', '-n', '-a', '-o', str(out / f'{name}.window.png')], check=True)
        time.sleep(1)
        return {'video': video, 'scale': hires.get('scale'),
                'hires_size': Image.open(out / f'{name}.hires.png').size}
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        log.close()


def diff_fraction(a, b):
    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    if ia.size != ib.size:
        return None
    hist = ImageChops.difference(ia, ib).convert('L').histogram()
    return 1 - hist[0] / sum(hist)


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'analysis/agent' / f'graphics-{stamp}'
    out.mkdir(parents=True)
    original = SETTINGS.read_text()
    results = {}
    try:
        for name, video in RUNS.items():
            SETTINGS.write_text(settings_with(original, video))
            results[name] = capture(name, video, out)
    finally:
        SETTINGS.write_text(original)
    results['texture_filter_hires_diff'] = diff_fraction(
        out / 'scale1_nearest_smooth.hires.png', out / 'scale1_bilinear_smooth.hires.png')
    results['smoothing_window_diff'] = diff_fraction(
        out / 'scale1_nearest_smooth.window.png', out / 'scale1_nearest_sharp.window.png')
    (out / 'results.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(out)


if __name__ == '__main__':
    main()
