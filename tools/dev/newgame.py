"""Wait (under turbo) until the 512-wide title screen shows, then confirm New Game and screenshot the result."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'psxrecomp', 'tools'))
from debug_client import query

OUT = os.path.dirname(os.path.abspath(__file__))
def cmd(name, **kw):
    return query('127.0.0.1', 4398, {'cmd': name, **kw})

cmd('turbo', enabled=1)
end = time.monotonic() + 180
while time.monotonic() < end:
    r = cmd('screenshot_file', path=f'{OUT}/ng_probe.png')
    if r.get('ok') and r.get('width') == 512:
        break
    time.sleep(0.2)
cmd('turbo', enabled=0)
print('title at frame', cmd('frame').get('frame'))
time.sleep(1.0)
btn = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x2000
cmd('input_route_clear')
cmd('input_route_append', frames=6, buttons=0xFFFF & ~btn)
cmd('input_route_append', frames=10, buttons=0xFFFF)
cmd('input_route_start')
for i in range(8):
    time.sleep(1.0)
    r = cmd('screenshot_file', path=f'{OUT}/ng{i}.png')
    print(i, cmd('frame').get('frame'), r.get('width'), r.get('error', ''))
