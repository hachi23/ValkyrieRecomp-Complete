#!/usr/bin/env python3
"""Add function_entry_pcs to overlay_captures.json so compile_overlays.py can
walk regions the runtime captured without any recorded function entry.

An executed PC becomes an entry when it is a direct `jal` target (from the
game EXE or any captured region), or it begins right after a `jr ra` and its
delay slot (skipping nop padding) and opens a stack frame or is a jal target.
Only PCs the game actually executed are added.

Usage: seed_overlay_entries.py <in.json> <out.json> [--exe disc/SLUS_011.56]
"""
import argparse, base64, json, struct

JR_RA = 0x03E00008


def words(data, base):
    for i in range(0, len(data) - 3, 4):
        yield base + i, struct.unpack_from('<I', data, i)[0]


def jal_target(w):
    return 0x80000000 | ((w & 0x03FFFFFF) << 2) if w >> 26 == 3 else None


def opens_frame(w):
    # addiu $sp, $sp, -imm
    return w >> 16 == 0x27BD and (w & 0x8000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--exe', default='disc/SLUS_011.56')
    a = ap.parse_args()
    caps = json.load(open(a.src))
    exe = open(a.exe, 'rb').read()
    load = struct.unpack_from('<I', exe, 0x18)[0]
    blobs = [(load, exe[0x800:])]
    for c in caps:
        blobs.append((int(c['load_addr'], 16), base64.b64decode(c['bytes_b64'])))
    jal_targets = {t for base, data in blobs for _, w in words(data, base) if (t := jal_target(w))}

    for c in caps:
        base = int(c['load_addr'], 16)
        data = base64.b64decode(c['bytes_b64'])[:c['size'] - c.get('guard_bytes', 0)]
        wmap = dict(words(data, base))
        executed = {int(x, 16) for x in c.get('executed_pcs', [])}
        found = set()
        for pc in executed:
            if pc not in wmap:
                continue
            if pc in jal_targets:
                found.add(pc)
                continue
            p = pc - 4
            while wmap.get(p) == 0 and p > base:
                p -= 4
            # p is now the delay slot (possibly a nop we skipped past) or real code
            after_return = wmap.get(p - 4) == JR_RA or wmap.get(p) == JR_RA
            if after_return and opens_frame(wmap[pc]):
                found.add(pc)
        old = {int(x, 16) for x in c.get('function_entry_pcs', [])}
        c['function_entry_pcs'] = [f'0x{x:08X}' for x in sorted(old | found)]
        print(f"{c['load_addr']}: executed={len(executed)} entries {len(old)} -> {len(c['function_entry_pcs'])}")
    json.dump(caps, open(a.dst, 'w'), indent=1)


if __name__ == '__main__':
    main()
