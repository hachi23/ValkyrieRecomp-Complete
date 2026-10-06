"""advance.py <rounds> <prefix> : under turbo, tap circle 30x per round, screenshot after each round."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'psxrecomp', 'tools'))
from debug_client import query

PORT = 4398
OUT = os.path.dirname(os.path.abspath(__file__))


def cmd(name, **kw):
    r = query('127.0.0.1', PORT, {'cmd': name, **kw})
    assert isinstance(r, dict), (name, r)
    return r


rounds, prefix = int(sys.argv[1]), sys.argv[2]
btn = 0x2000 if len(sys.argv) < 4 else int(sys.argv[3], 0)
cmd('turbo', enabled=1)
try:
    for n in range(rounds):
        cmd('input_route_clear')
        for _ in range(30):
            cmd('input_route_append', frames=4, buttons=0xFFFF & ~btn)
            cmd('input_route_append', frames=16, buttons=0xFFFF)
        cmd('input_route_start')
        while cmd('input_route_status').get('active'):
            time.sleep(0.1)
        cmd('clear_input')
        r = cmd('screenshot_file', path=f'{OUT}/{prefix}{n}.png')
        print(n, cmd('frame').get('frame'), r.get('ok'), r.get('error', ''))
finally:
    cmd('turbo', enabled=0)
    cmd('clear_input')
