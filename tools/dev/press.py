"""press.py <btn>[:frames] ... [--shot name] [--wait secs]
Queue button presses (each followed by 20 neutral frames), run them, optionally screenshot.
Buttons: start select up down left right cross circle square triangle l1 l2 r1 r2 wait"""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'psxrecomp', 'tools'))
from debug_client import query

PORT = 4398
OUT = os.path.dirname(os.path.abspath(__file__))
BITS = dict(select=0x0001, l3=0x0002, r3=0x0004, start=0x0008, up=0x0010, right=0x0020, down=0x0040,
            left=0x0080, l2=0x0100, r2=0x0200, l1=0x0400, r1=0x0800, triangle=0x1000, circle=0x2000,
            cross=0x4000, square=0x8000, wait=0)


def cmd(name, **kw):
    r = query('127.0.0.1', PORT, {'cmd': name, **kw})
    assert isinstance(r, dict) and r.get('ok'), (name, r)
    return r


shot, wait_s, presses = None, 1.0, []
args = sys.argv[1:]
i = 0
while i < len(args):
    a = args[i]
    if a == '--shot':
        shot = args[i + 1]; i += 2; continue
    if a == '--wait':
        wait_s = float(args[i + 1]); i += 2; continue
    name, _, fr = a.partition(':')
    mask = 0
    for part in name.split('+'):
        mask |= BITS[part]
    presses.append((mask, int(fr or 6)))
    i += 1

cmd('input_route_clear')
for mask, fr in presses:
    cmd('input_route_append', frames=fr, buttons=0xFFFF & ~mask)
    if mask:
        cmd('input_route_append', frames=20, buttons=0xFFFF)
cmd('input_route_append', frames=2, buttons=0xFFFF)
cmd('input_route_start')
end = time.monotonic() + 120
while time.monotonic() < end:
    st = cmd('input_route_status')
    if not st.get('active', st.get('running', False)):
        break
    time.sleep(0.1)
cmd('clear_input')
time.sleep(wait_s)
f = cmd('frame')['frame']
if shot:
    r = cmd('screenshot_file', path=f'{OUT}/{shot}.png')
    print(f'frame {f} shot {shot}.png {r["width"]}x{r["height"]}')
else:
    print(f'frame {f}')
