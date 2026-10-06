#!/usr/bin/env python3
"""Record the disc-loaded code (overlays) the game runs in each checkpoint scene.

One fresh game process per save-state slot, with [runtime] overlay_cache = true
in a temporary game.toml next to the exe. The recorder only tracks RAM ranges
filled by CD reads, and restoring a save state is not one, so every non-movie
slot is primed by playing the movie checkpoint (slot 10) first. Results are
merged into analysis/performance/overlay/overlay_captures.json, on top of
captures-pass1.json when it exists.

Next steps: tools/seed_overlay_entries.py, then compile_overlays.py --static
into generated/overlays/ (see docs/PERFORMANCE_FINDINGS.md)."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build-perf'
OUT = ROOT / 'analysis/performance/overlay'
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query
PORT = 4397
SLOTS = [(int(a), int(b)) for a, b in (x.split(":") for x in os.environ.get("SLOTS", "10:90,3:45,5:45,1:20,2:30,4:30").split(","))]
BASE = OUT / 'captures-pass1.json'
DUMPS_AT = [4, 8, 12, 20, 30, 45, 60, 90]

def cmd(name, **kw):
    r = query('127.0.0.1', PORT, {'cmd': name, **kw})
    assert isinstance(r, dict) and r.get('ok') is True, (name, r)
    return r

def wait(fn, secs):
    end = time.monotonic() + secs
    while time.monotonic() < end:
        try:
            v = fn()
            if v: return v
        except Exception: pass
        time.sleep(0.25)
    raise TimeoutError

def load(slot):
    gen = cmd('savestate_status')['generation']
    cmd('savestate', op='load', slot=slot)
    st = wait(lambda: (s := cmd('savestate_status'))['generation'] != gen and s, 60)
    assert st['last_ok'] == 1, st

def run_slot(slot, secs):
    state = OUT / 'state'
    shutil.rmtree(state, ignore_errors=True)
    shutil.copytree(ROOT / 'analysis/performance/fps-fix/state', state)
    (BUILD / 'overlay_captures.json').unlink(missing_ok=True)
    with (OUT / f'capture-slot{slot}.log').open('w') as log:
        p = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT),
                              '--memcard-dir', str(state), '--renderer', 'vulkan', '--disc',
                              str(ROOT / 'disc/Disc1/Valkyrie Profile (Undub) (Disc 1).cue')],
                             cwd=BUILD, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            wait(lambda: cmd('ping'), 60)
            time.sleep(3)
            if slot != 10:
                load(10)     # movie streams from CD, which marks the code ranges
                time.sleep(8)
            load(slot)
            # Dump several times: a region's bytes are whatever occupies it at
            # dump time, so a long scene must be sampled before its code is
            # replaced (the movie's decode loop is gone by the end).
            caps, start = [], time.monotonic()
            for t in DUMPS_AT:
                if t > secs: break
                time.sleep(max(0, start + t - time.monotonic()))
                d = cmd('overlay_capture_dump')
                caps += json.loads((BUILD / 'overlay_captures.json').read_text())
                print(json.dumps({'slot': slot, 't': t, 'entries': d['capture_entries']}), flush=True)
        finally:
            p.terminate(); p.wait(timeout=15)
    (OUT / f'captures-slot{slot}.json').write_text(json.dumps(caps))
    return caps


cfg = BUILD / 'game.toml'
orig = cfg.read_text()
cfg.write_text(orig.replace('[runtime]\n', '[runtime]\noverlay_cache = true\n', 1))
env = {**os.environ, 'DRI_PRIME': 'pci-0000_01_00_0!', 'PSX_BIOS_HLE': '0', 'PSX_DISPLAY_RING': '0'}
try:
    merged = {}
    for c in (json.loads(BASE.read_text()) if BASE.exists() else []):
        merged[(c['load_addr'], c['bytes_b64'])] = c
    for slot, secs in SLOTS:
        for c in run_slot(slot, secs):
            key = (c['load_addr'], c['bytes_b64'])
            if key in merged:
                m = merged[key]
                for k in ('executed_pcs', 'dispatch_entry_pcs', 'function_entry_pcs'):
                    m[k] = sorted(set(m.get(k, [])) | set(c.get(k, [])))
                m['seeds'] = m['dispatch_entry_pcs']
            else:
                merged[key] = c
    (OUT / 'overlay_captures.json').write_text(json.dumps(list(merged.values()), indent=1))
    print('merged regions', len(merged))
finally:
    cfg.write_text(orig)
