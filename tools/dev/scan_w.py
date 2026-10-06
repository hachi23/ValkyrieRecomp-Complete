"""scan_w.py <file> <base_hex> [skip_hex]
Find MIPS compare/offset instructions whose immediate looks like a screen-width bound."""
import sys, struct

f, base = sys.argv[1], int(sys.argv[2], 16)
skip = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0
data = open(f, 'rb').read()[skip:]
OPS = {0x0A: 'slti', 0x0B: 'sltiu', 0x09: 'addiu', 0x08: 'addi', 0x0D: 'ori'}
# Screen width 320 and nearby margins; 160 = half width (centre); 256/384/512 common for wider bounds
WATCH = {0x140, 0x13F, 0x141, 0x150, 0x160, 0x170, 0x180, 0x1A0, 0x1C0, 0x1C1, 0x200, 0xA0, 0x120}
hits = {}
for i in range(0, len(data) - 3, 4):
    w = struct.unpack_from('<I', data, i)[0]
    op = w >> 26
    if op not in OPS:
        continue
    imm = w & 0xFFFF
    neg = (-imm) & 0xFFFF  # e.g. addiu x,x,-320
    sval = imm - 0x10000 if imm & 0x8000 else imm
    if imm in WATCH or (op in (0x09, 0x08) and neg in WATCH and imm & 0x8000):
        if op == 0x09 and imm in (0xA0, 0x120, 0x200, 0x180):
            continue  # too common as plain struct offsets
        rs, rt = (w >> 21) & 31, (w >> 16) & 31
        addr = base + i
        print(f'0x{addr:08X}: {OPS[op]:5s} r{rt}, r{rs}, {sval}  (0x{w:08X})')
        hits[OPS[op]] = hits.get(OPS[op], 0) + 1
print('totals:', hits)
