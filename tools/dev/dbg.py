"""Tiny wrapper: dbg.py <cmd> [key=value ...]  -> prints JSON reply from the game's debug server."""
import os
import json, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'psxrecomp', 'tools'))
from debug_client import query

PORT = 4398
args = {'cmd': sys.argv[1]}
for kv in sys.argv[2:]:
    k, v = kv.split('=', 1)
    try:
        v = int(v, 0)
    except ValueError:
        pass
    args[k] = v
r = query('127.0.0.1', PORT, args)
s = json.dumps(r)
print(s if len(s) < 4000 else s[:4000] + '...')
