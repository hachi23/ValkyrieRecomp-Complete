#!/usr/bin/env python3
"""Drive the launcher's cheat editor with LNG_SCRIPT and check the saved list.

Run 1 pastes three cheats (one new, one with a bad code, one duplicate), adds
them, deletes a bundled cheat, and imports a RetroArch .cht file. Run 2
replaces the whole list from a [Name]-block file. The cheat list and
settings.toml are restored afterwards.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build-linux'
LIST = ROOT / 'cheats/SLUS-01156.toml'
SETTINGS = BUILD / 'settings.toml'
OUT = ROOT / 'analysis/agent/cheat-editor'

CODES_BOX = '640,926'
ADD_WITH_CHECK_LINE = '118,1039'
IMPORT = '251,1012'
REPLACE = '400,1012'
DELETE_FIRST_ROW = '388,530'


def ids(text):
    return [line.split('"')[1] for line in text.splitlines() if line.startswith('id = ')]


def run(script):
    env = {**os.environ, 'PSX_BIOS_HLE': '0', 'LNG_SCRIPT': script}
    subprocess.run(['./ValkyrieRecomp', '--launcher'], cwd=BUILD, env=env, timeout=90,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original_list, original_settings = LIST.read_text(), SETTINGS.read_text()
    cht = OUT / 'retroarch.cht'
    cht.write_text('cheats = 2\n'
                   'cheat0_desc = "Max Gold"\ncheat0_code = "80050000 FFFF"\n'
                   'cheat1_desc = "Max Materialize"\ncheat1_code = "800E4A2C 270F+800E4A2E 0000"\n')
    blocks = OUT / 'blocks.txt'
    blocks.write_text('[Walk Through Walls]\nType = Gameshark\n800A1234 2400\n')
    r = {'before': ids(original_list)}
    try:
        paste = 'Max Gold\\n80050000 FFFF\\nBad One\\n90050000 0001\\nDup\\nD005A7BC FFFF\\n8005A7BC 0000\\n'
        run(f'size:1280x1500;wait:20;view:assist_tools;wait:20;click:{CODES_BOX};wait:5;'
            f'type:{paste};wait:20;shot:{OUT}/1_pasted.png;click:{ADD_WITH_CHECK_LINE};wait:20;'
            f'shot:{OUT}/2_added.png;click:{DELETE_FIRST_ROW};wait:5;click:{DELETE_FIRST_ROW};wait:20;'
            f'pickfile:{cht};click:{IMPORT};wait:20;shot:{OUT}/3_imported.png;quit')
        r['after_add_delete_import'] = ids(LIST.read_text())
        run(f'size:1280x1500;wait:20;view:assist_tools;wait:20;click:{REPLACE};wait:5;'
            f'pickfile:{blocks};click:{REPLACE};wait:20;shot:{OUT}/4_replaced.png;quit')
        r['after_replace'] = ids(LIST.read_text())
        backup = Path(str(LIST) + '.bak')
        r['backup_ids'] = ids(backup.read_text()) if backup.exists() else None
    finally:
        LIST.write_text(original_list)
        SETTINGS.write_text(original_settings)
        Path(str(LIST) + '.bak').unlink(missing_ok=True)
    print(json.dumps(r, indent=2))


if __name__ == '__main__':
    main()
