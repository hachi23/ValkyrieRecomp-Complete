"""Live feasibility test: raise every 'x < 320' compare in loaded field code to 'x < 400'.
Usage: widen_test.py scan | patch | revert"""
import os
import sys, struct, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'psxrecomp', 'tools'))
from debug_client import query

LO, HI = 0x80030000, 0x800C0000   # loaded game code (data above 0x80100000 skipped)
NEW = 400
MODE = sys.argv[2] if len(sys.argv) > 2 else 'compares'


def cmd(name, **kw):
    r = query('127.0.0.1', 4398, {'cmd': name, **kw})
    assert isinstance(r, dict) and r.get('ok'), (name, r)
    return r


def sites():
    data = bytes.fromhex(cmd('read_ram', addr=f'0x{LO:08X}', len=HI - LO)['hex'])
    out = []
    for i in range(0, len(data), 4):
        w = struct.unpack_from('<I', data, i)[0]
        op, imm = w >> 26, w & 0xFFFF
        if op in (0x0A, 0x0B) and imm in (0x140, 0x141):   # slti / sltiu  rt, rs, 320|321
            out.append((LO + i, w))
        elif MODE == 'loads' and op == 0x09 and ((w >> 21) & 31) == 0 and imm == 0x140:  # addiu rt, r0, 320
            out.append((LO + i, w))
    return out


op = sys.argv[1]
s = sites()
print(f'{len(s)} compare sites found')
if op == 'scan':
    for a, w in s:
        print(f'0x{a:08X} 0x{w:08X}')
elif op == 'patch':
    for a, w in s:
        imm = w & 0xFFFF
        new = NEW + (imm - 0x140)
        cmd('write_ram', addr=f'0x{a:08X}', val=f'0x{new & 0xFF:02X}')
        cmd('write_ram', addr=f'0x{a+1:08X}', val=f'0x{new >> 8:02X}')
    print('patched', len(s), 'sites to', NEW)
    json.dump([[a, w] for a, w in s], open(__file__ + '.sites.json', 'w'))
elif op == 'revert':
    for a, w in json.load(open(__file__ + '.sites.json')):
        cmd('write_ram', addr=f'0x{a:08X}', val=f'0x{w & 0xFF:02X}')
        cmd('write_ram', addr=f'0x{a+1:08X}', val=f'0x{(w >> 8) & 0xFF:02X}')
    print('reverted')
