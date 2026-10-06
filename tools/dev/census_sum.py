"""Summarise one frame of the draw census: how many prims start in each 32-px column band."""
import csv, sys, collections
rows = list(csv.DictReader(open(sys.argv[1])))
f0 = rows[0]['frame']
rows = [r for r in rows if r['frame'] == f0]
bands = collections.Counter()
ops = collections.Counter()
xs = []
for r in rows:
    x = int(r['x']); xs.append(x)
    bands[(x // 32) * 32] += 1
    ops[r['opcode']] += 1
print('frame', f0, 'prims', len(rows), 'x range', min(xs), '..', max(xs))
print('opcodes', dict(ops))
for b in sorted(bands):
    print(f'{b:5d}..{b+31:<5d} {bands[b]:4d} ' + '#' * min(60, bands[b] // 2))
