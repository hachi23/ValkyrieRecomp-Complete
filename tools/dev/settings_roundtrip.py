"""Round-trip settings.toml through the real launcher and report every lost field.

settings_roundtrip.py [--profile N] [--exe EXE] [--save BASELINE] [--compare BASELINE]

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

PROFILE_1 = f'''
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

PROFILE_2 = f'''
[video]
renderer          = "opengl"
supersampling     = 2
window_width      = 0
antialiasing      = true
texture_filtering = "bilinear"
texture_dedither  = false
stretch           = false
fmv_filter        = "nearest"
geometry_correction   = false
perspective_texturing = false
crt_filter        = "trinitron"
scanlines         = false
scanline_strength = 0.75
fast_boot         = false
bios_hle          = true
fullscreen        = 0
frame_interpolation = false
frame_interpolation_fps = 0
aspect_ratio      = "4:3"
rewind            = false
rewind_depth      = 200
rewind_interval   = 1

[audio]
frequency = 44100
spu_hq = false

[hotkeys]
rewind_pad = 0
save_state_menu_pad = 0
fast_forward_pad = 0
fast_forward_toggle_pad = 0
quick_menu_pad = 0
disc_swap_pad = 0

[launcher]
skip_launcher = false

[disc]
path = "{DISC}"
selected = 1

[memcard]
dir     = "saves"
enable1 = false
enable2 = true

[controller]
p1_device = "none"
p1_mode   = "digital"
multitap  = true
multitap_analog = true

[localization]
language = "en"
'''
PROFILES = {1: (PROFILE_1, {'scanlines': 1, 'strength_pct': 30}),
            2: (PROFILE_2, {'scanlines': 0, 'strength_pct': 75})}


def make_install(dest, settings, exe):
    for name in os.listdir(BUILD):
        src = os.path.join(BUILD, name)
        if name.endswith('.dll') or name in ('game.toml', 'game_options.toml'):
            shutil.copy2(src, dest)
        elif name in ('assets', 'bios', 'cheats', 'mods'):
            shutil.copytree(src, os.path.join(dest, name))
    shutil.copy2(exe, os.path.join(dest, 'ValkyrieRecomp.exe'))
    os.makedirs(os.path.join(dest, 'saves'))
    with open(os.path.join(dest, 'settings.toml'), 'w', encoding='utf-8') as f:
        f.write(settings)


def debug_query(cmd):
    return query('127.0.0.1', DEBUG_PORT, {'cmd': cmd})


def run_game(dest, direct):
    env = dict(os.environ, LNG_UI_SCALE='100', PSX_BIOS_HLE='0',
               LNG_SCRIPT=f'wait:60;click:{PLAY_BUTTON[0]},{PLAY_BUTTON[1]};wait:5')
    mode = '--no-launcher' if direct else '--launcher'
    proc = subprocess.Popen([os.path.join(dest, 'ValkyrieRecomp.exe'), mode,
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
    ap.add_argument('--profile', type=int, default=1, choices=sorted(PROFILES))
    ap.add_argument('--exe', default=os.path.join(BUILD, 'ValkyrieRecomp.exe'))
    ap.add_argument('--direct', action='store_true',
                    help='start without the launcher; settings.toml must stay untouched')
    ap.add_argument('--save')
    ap.add_argument('--compare')
    args = ap.parse_args()

    ok = True
    dest = tempfile.mkdtemp(prefix='settings_rt_')
    try:
        settings, expect_live = PROFILES[args.profile]
        make_install(dest, settings, args.exe)
        live = run_game(dest, args.direct)
        with open(os.path.join(dest, 'settings.toml'), encoding='utf-8') as f:
            written = f.read().replace(DISC, '<DISC>')
    finally:
        shutil.rmtree(dest, ignore_errors=True)

    if args.direct and written != settings.replace(DISC, '<DISC>'):
        print('FAIL a direct start rewrote settings.toml')
        ok = False
    sent = flatten(tomllib.loads(settings))
    got = flatten(tomllib.loads(written))
    for key in sorted(sent):
        if key not in got:
            print(f'LOST     {key} (sent {sent[key]!r})')
        elif got[key] != sent[key] and not key.endswith(('.path', '.dir')):
            print(f'CHANGED  {key}: sent {sent[key]!r}, got {got[key]!r}')
    print(f'game after PLAY: {live}')
    if not live or any(live.get(k) != v for k, v in expect_live.items()):
        print(f'FAIL game did not apply {expect_live}')
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
