#!/usr/bin/env python3
"""Check the session log, crash history and the next-launch crash notice.

Run 1 restores first_field, turns on battle-item-use, and calls force_crash.
Run 2 opens the launcher, captures it, ticks Safe mode and presses Play, then
exits cleanly. settings.toml is restored afterwards.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query

BUILD = ROOT / 'build-linux'
LOGS = BUILD / 'logs'
SETTINGS = BUILD / 'settings.toml'
OUT = ROOT / 'analysis/agent/crash-log'
PORT = 4395


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


def crashes():
    return sorted((LOGS / 'crashes').glob('crash-*.json'))


def sessions():
    return sorted(LOGS.glob('session-*.log'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original = SETTINGS.read_text()
    env = {**os.environ, 'PSX_BIOS_HLE': '0'}
    r = {}
    try:
        crashes_before = crashes()
        proc = subprocess.Popen(['./ValkyrieRecomp', '--no-launcher', '--debug-port', str(PORT)],
                                cwd=BUILD, stdout=open(OUT / 'run1.log', 'w'),
                                stderr=subprocess.STDOUT, env=env)
        wait_until(lambda: command('ping'), 30, 'debug server did not answer')
        before = command('savestate_status')['generation']
        command('savestate', op='load', slot=3)
        wait_until(lambda: command('savestate_status')['generation'] != before, 30, 'load receipt missing')
        command('cheats_assist', enabled=1)
        command('cheats_set', cheat='battle-item-use', enabled=1)
        time.sleep(1)
        try:
            command('force_crash')
        except Exception:
            pass
        proc.wait(timeout=30)
        r['run1_exit'] = proc.returncode
        new = [c for c in crashes() if c not in crashes_before]
        r['new_crash_files'] = [c.name for c in new]
        report = json.loads(new[-1].read_text())
        r['crash_reason'] = report['reason']
        r['crash_active_cheats'] = report['active_cheats']
        r['crash_cheat_changes'] = report['cheat_changes_last_600_frames']
        r['crash_last_state_load'] = report['last_state_load']
        r['crash_session_log'] = report['session_log']
        r['marker_after_crash'] = (LOGS / 'running.txt').read_text()
        r['session_log_tail'] = Path(report['session_log']).read_text().splitlines()[-8:]

        script = (f'size:1280x900;wait:30;shot:{OUT}/launcher_after_crash.png;'
                  'click:64,364;wait:10;click:1150,838;wait:60')
        proc = subprocess.Popen(['./ValkyrieRecomp', '--launcher', '--debug-port', str(PORT)],
                                cwd=BUILD, stdout=open(OUT / 'run2.log', 'w'),
                                stderr=subprocess.STDOUT, env={**env, 'LNG_SCRIPT': script})
        wait_until(lambda: command('ping'), 60, 'run 2 debug server did not answer')
        time.sleep(2)
        r['run2_cheats'] = {k: command('cheats_status')[k] for k in ('assist', 'safe_mode', 'writes_enabled')}
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=30)
        r['marker_after_clean_exit'] = (LOGS / 'running.txt').exists()
        r['run2_log_tail'] = sessions()[-1].read_text().splitlines()[-3:]
        r['session_files_kept'] = len(sessions())
    finally:
        SETTINGS.write_text(original)
    print(json.dumps(r, indent=2))


if __name__ == '__main__':
    main()
