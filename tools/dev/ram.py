"""ram.py dump <addr> <len> <file>   |  ram.py find <file> <base> <value>  |  ram.py diff <a> <b> <base>"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'psxrecomp', 'tools'))
from debug_client import query

op = sys.argv[1]
if op == 'dump':
    addr, n, f = sys.argv[2], int(sys.argv[3], 0), sys.argv[4]
    r = query('127.0.0.1', 4398, {'cmd': 'read_ram', 'addr': addr, 'len': n})
    open(f, 'wb').write(bytes.fromhex(r['hex']))
    print('dumped', n, 'bytes from', r['addr'])
elif op == 'find':
    data, base, v = open(sys.argv[2], 'rb').read(), int(sys.argv[3], 0), int(sys.argv[4], 0)
    for i in range(len(data)):
        if data[i] == v:
            h = int.from_bytes(data[i:i+2], 'little') if i % 2 == 0 else None
            print(f'0x{base+i:08X} byte={v}' + (f' half={h}' if h is not None else ''))
elif op == 'diff':
    a, b, base = open(sys.argv[2], 'rb').read(), open(sys.argv[3], 'rb').read(), int(sys.argv[4], 0)
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print(f'0x{base+i:08X} {x} -> {y}')
