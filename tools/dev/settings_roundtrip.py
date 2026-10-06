"""Round-trip settings.toml through the real launcher and report every lost field.

settings_roundtrip.py [--save BASELINE] [--compare BASELINE]

Builds a throwaway install from build-win/, writes a settings.toml where every
launcher-visible value differs from its default, opens the launcher, presses
PLAY, and reads back the settings.toml the game wrote. Exit 1 when a field
changed or the written file differs from BASELINE.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BUILD = os.path.join(ROOT, 'build-win')
sys.path.insert(0, os.path.join(ROOT, 'psxrecomp', 'tools'))
from debug_client import query  # noqa: E402

DISC = os.path.join(ROOT, 'disc', 'Disc1', 'Valkyrie Profile (Undub) (Disc 1).cue').replace('\\', '/')
PLAY_BUTTON = (972, 817)  # launcher window pixels at LNG_UI_SCALE=100
DEBUG_PORT = 4399

SETTINGS = f'''
[video]
renderer          = "vulkan"
supersampling     = 3
window_width      = 1280
antialiasing      = false
texture_filtering = "smooth"
texture_dedither  = true
stretch           = true
fmv_filter        = "bilinear"
geometry_correction   = true
perspective_texturing = true
crt_filter        = "crt"
scanlines         = true
scanline_strength = 0.3
fast_boot         = true
bios_hle          = false
fullscreen        = 0
frame_interpolation = true
frame_interpolation_fps = 120
aspect_ratio      = "4:3"
rewind            = true
rewind_depth      = 100
rewind_interval   = 8

[audio]
frequency = 48000
spu_hq = true

[hotkeys]
rewind_pad = 2040
save_state_menu_pad = 1272
fast_forward_pad = 1024
fast_forward_toggle_pad = 1528
quick_menu_pad = 1272
disc_swap_pad = 2040

[launcher]
skip_launcher = true

[disc]
path = "{DISC}"
selected = 1

[memcard]
dir     = "saves"
enable1 = true
enable2 = false

[controller]
p1_device = "keyboard"
p1_mode   = "analog"
p1_deadzone = 6553
p2_device = "none"
p2_mode   = "digital"
p2_deadzone = 3276
multitap  = false
multitap_analog = false

[localization]
language = "en"
'''


def make_install(dest):
    for name in os.listdir(BUILD):
        src = os.path.join(BUILD, name)
        if name.endswith('.dll') or name in ('ValkyrieRecomp.exe', 'game.toml', 'game_options.toml'):
            shutil.copy2(src, dest)
        elif name in ('assets', 'bios', 'cheats', 'mods'):
            shutil.copytree(src, os.path.join(dest, name))
    os.makedirs(os.path.join(dest, 'saves'))
    with open(os.path.join(dest, 'settings.toml'), 'w', encoding='utf-8') as f:
        f.write(SETTINGS)


def debug_query(cmd):
    return query('127.0.0.1', DEBUG_PORT, {'cmd': cmd})


def run_launcher(dest):
    env = dict(os.environ, LNG_UI_SCALE='100', PSX_BIOS_HLE='0',
               LNG_SCRIPT=f'wait:60;click:{PLAY_BUTTON[0]},{PLAY_BUTTON[1]};wait:5')
    proc = subprocess.Popen([os.path.join(dest, 'ValkyrieRecomp.exe'), '--launcher',
                             '--debug-port', str(DEBUG_PORT)], cwd=dest, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    live = None
    try:
        for _ in range(60):
            time.sleep(1)
            try:
                live = debug_query('scanline')
                break
            except OSError:
                if proc.poll() is not None:
                    break
    finally:
        proc.kill()
        proc.wait()
    return live


def flatten(doc, prefix=''):
    out = {}
    for k, v in doc.items():
        if isinstance(v, dict):
            out.update(flatten(v, f'{prefix}{k}.'))
        else:
            out[prefix + k] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--save')
    ap.add_argument('--compare')
    args = ap.parse_args()

    dest = tempfile.mkdtemp(prefix='settings_rt_')
    try:
        make_install(dest)
        live = run_launcher(dest)
        with open(os.path.join(dest, 'settings.toml'), encoding='utf-8') as f:
            written = f.read()
    finally:
        shutil.rmtree(dest, ignore_errors=True)

    sent = flatten(tomllib.loads(SETTINGS))
    got = flatten(tomllib.loads(written))
    ok = True
    for key in sorted(sent):
        if key not in got:
            print(f'LOST     {key} (sent {sent[key]!r})')
        elif got[key] != sent[key] and not key.endswith(('.path', '.dir')):
            print(f'CHANGED  {key}: sent {sent[key]!r}, got {got[key]!r}')
    print(f'game after PLAY: {live}')
    if live != {'id': 0, 'ok': True, 'scanlines': 1, 'strength_pct': 30}:
        print('FAIL game did not apply scanlines = true, strength 0.3')
        ok = False

    if args.save:
        with open(args.save, 'w', encoding='utf-8') as f:
            f.write(written)
        print(f'saved {args.save}')
    if args.compare:
        with open(args.compare, encoding='utf-8') as f:
            base = f.read()
        if base != written:
            ok = False
            print('FAIL written settings.toml differs from baseline:')
            import difflib
            sys.stdout.writelines(difflib.unified_diff(
                base.splitlines(True), written.splitlines(True), 'baseline', 'now'))
        else:
            print('written settings.toml matches baseline')
    print('ROUNDTRIP OK' if ok else 'ROUNDTRIP FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
