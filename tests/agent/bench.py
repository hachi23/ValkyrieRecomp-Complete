#!/usr/bin/env python3
"""Fixed-work performance run: movie, first field, world map.

Usage: bench.py <label> [--exe PATH]
Writes analysis/performance/runs/<label>.json. Each scene restores a slot,
warms 60 guest frames, then times a fixed number of guest frames."""
import argparse, ctypes, ctypes.util, json, os, shutil, statistics, subprocess, sys, time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'game.toml').exists())
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query

BUILD = Path(os.environ.get('BENCH_BUILD', ROOT / 'build-perf'))
RUNS = ROOT / 'analysis/performance/runs'
STATE = ROOT / 'analysis/performance/fps-fix/state'
DISC = ROOT / 'disc/Disc1/Valkyrie Profile (Undub) (Disc 1).cue'
PORT = 4398
DEVICE = 'vulkan device AMD Radeon RX Graphics (RADV POLARIS11)'
SCENES = [('movie', 10, 240), ('field', 3, 600), ('map', 5, 300)]
SDL = ctypes.CDLL(ctypes.util.find_library('SDL3'))
SDL.SDL_GetPerformanceFrequency.restype = ctypes.c_uint64
FREQ = SDL.SDL_GetPerformanceFrequency()


def cmd(name, **kw):
    r = query('127.0.0.1', PORT, {'cmd': name, **kw})
    assert isinstance(r, dict) and r.get('ok'), (name, r)
    return r


def wait(fn, secs, what):
    end = time.monotonic() + secs
    while time.monotonic() < end:
        try:
            v = fn()
            if v:
                return v
        except (OSError, AssertionError, ValueError):
            pass
        time.sleep(0.05)
    raise TimeoutError(what)


def rss_peak(pid):
    for line in Path(f'/proc/{pid}/status').read_text().splitlines():
        if line.startswith('VmHWM:'):
            return int(line.split()[1])


def dispatch():
    s = cmd('overlay_loader_status')
    return {k: s.get(k, 0) for k in ('dispatch_native', 'dispatch_interp_fallback', 'static_hits', 'static_checks')}


def scene(slot, frames):
    gen = cmd('savestate_status')['generation']
    t0 = time.monotonic()
    cmd('savestate', op='load', slot=slot)
    wait(lambda: cmd('savestate_status')['generation'] != gen, 30, 'load receipt')
    load_s = time.monotonic() - t0
    assert cmd('savestate_status')['last_ok'] == 1
    f = cmd('frame')['frame']
    wait(lambda: cmd('frame')['frame'] >= f + 60, 60, 'warm frames')
    anchor = cmd('vk_perf', count=256)['vk_perf'][-1]
    rows = {anchor['f']: anchor}
    fmv0, d0 = cmd('fmv_state'), dispatch()
    f0, t0 = cmd('frame')['frame'], time.monotonic()
    while cmd('frame')['frame'] < f0 + frames:
        time.sleep(0.25)
        rows.update({r['f']: r for r in cmd('vk_perf', count=256)['vk_perf'] if r['f'] > anchor['f']})
    elapsed = time.monotonic() - t0
    f1, fmv1, d1 = cmd('frame')['frame'], cmd('fmv_state'), dispatch()
    data = sorted(rows.values(), key=lambda r: r['f'])
    iv = [(b['qpc'] - a['qpc']) * 1000 / FREQ for a, b in zip(data, data[1:]) if b['f'] == a['f'] + 1]
    out = {'load_s': round(load_s, 3), 'elapsed_s': round(elapsed, 3),
           'guest_fps': round((f1 - f0) / elapsed, 2),
           'present_median_ms': round(statistics.median(iv), 3),
           'present_p95_ms': round(sorted(iv)[int(.95 * (len(iv) - 1))], 3),
           'present_fps': round(1000 / statistics.mean(iv), 2),
           'dispatch': {k: d1[k] - d0[k] for k in d1}}
    if 'mdec_decode_count' in fmv1:
        out['movie_images_per_s'] = round((fmv1['mdec_decode_count'] - fmv0['mdec_decode_count']) / elapsed, 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('label')
    ap.add_argument('--exe', default=str(BUILD / 'ValkyrieRecomp'))
    a = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    work = RUNS / f'{a.label}.state'
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(STATE, work)
    logs_before = set((BUILD / 'logs').glob('session-*.log'))
    env = {**os.environ, 'DRI_PRIME': 'pci-0000_01_00_0!', 'PSX_BIOS_HLE': '0'}
    t0 = time.monotonic()
    with (RUNS / f'{a.label}.log').open('w') as log:
        p = subprocess.Popen([a.exe, '--no-launcher', '--debug-port', str(PORT), '--memcard-dir', str(work),
                              '--renderer', 'vulkan', '--disc', str(DISC)],
                             cwd=BUILD, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            wait(lambda: cmd('ping'), 60, 'debug server')
            rec = {'label': a.label, 'exe': a.exe, 'startup_s': round(time.monotonic() - t0, 3)}
            def session():
                new = sorted(set((BUILD / 'logs').glob('session-*.log')) - logs_before)
                return new and DEVICE in new[-1].read_text() and new[-1]
            rec['device_ok'] = bool(wait(session, 60, 'RX 560X line'))
            rec['scenes'] = {n: scene(s, fr) for n, s, fr in SCENES}
            rec['rss_peak_kib'] = rss_peak(p.pid)
        finally:
            p.terminate()
            p.wait(timeout=15)
    shutil.rmtree(work, ignore_errors=True)
    (RUNS / f'{a.label}.json').write_text(json.dumps(rec, indent=2) + '\n')
    print(json.dumps(rec, indent=2))


if __name__ == '__main__':
    main()
