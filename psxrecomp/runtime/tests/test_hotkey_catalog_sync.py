"""The runtime and the launcher must agree on every hotkey's [KeyMap] key and default.

psxrecomp/runtime/src/host_keymap.c (kCatalog) is what the game obeys.
recomp-ui/src/common/launcher_hotkeys.def is what the launcher shows and
writes. A key spelled differently, or a different default, silently breaks
that hotkey, so this compares the two tables row by row.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME_SRC = os.path.join(HERE, '..', 'src', 'host_keymap.c')
LAUNCHER_DEF = os.path.join(HERE, '..', '..', '..', 'recomp-ui', 'src', 'common',
                            'launcher_hotkeys.def')


def norm(bind):
    return ', '.join(t.strip() for t in bind.split(',') if t.strip())


def runtime_catalog():
    text = open(RUNTIME_SRC, encoding='utf-8').read()
    rows = {}
    for key, default in re.findall(r'\[HOST_KEYMAP_\w+\]\s*=\s*\{"(\w+)",\s*"([^"]*)"\}', text):
        rows.setdefault(key, norm(default))  # first row wins: the full-feature build
    return rows


def launcher_catalog():
    text = open(LAUNCHER_DEF, encoding='utf-8').read()
    return {key: norm(default) for _, key, default, _ in
            re.findall(r'LNG_HOTKEY\((\w+),\s*"(\w+)",\s*"([^"]*)",\s*"([^"]*)"\)', text)}


@unittest.skipUnless(os.path.exists(LAUNCHER_DEF), 'recomp-ui not present')
class HotkeyCatalogSync(unittest.TestCase):
    def test_every_runtime_hotkey_matches_the_launcher(self):
        runtime = runtime_catalog()
        launcher = launcher_catalog()
        self.assertEqual(len(runtime), 12)
        for key, default in runtime.items():
            self.assertIn(key, launcher, f'launcher has no row for [KeyMap] {key}')
            self.assertEqual(launcher[key], default, f'[KeyMap] {key} default differs')


if __name__ == '__main__':
    sys.exit(unittest.main())
