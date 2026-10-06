# tools/dev

Helper scripts for building, running and testing on the Windows PC (MSYS2
MinGW64 + Vulkan SDK 1.4.363.0). Run the `.sh` files with
`C:\msys64\usr\bin\bash.exe -l tools/dev/<script>`; they find the repo root
themselves.

| Script | What it does |
|---|---|
| `env.sh` | Shared MinGW64 + Vulkan environment, `cd` to the repo root |
| `gen.sh` | Build the emitters, verify both discs, generate the game C into `generated/` |
| `bios.sh` | Regenerate the OpenBIOS C, then build |
| `build.sh` | Configure `build-win/` if needed and build `psx-runtime` (log: `build.log`) |
| `deps.sh` | Copy the MinGW DLLs the exe needs into `build-win/` (needed after a fresh `build-win`) |
| `dbg.py <cmd> k=v` | One debug-server command (port 4398) |
| `press.py`, `advance.py`, `newgame.py` | Queue pad input routes through the debug server |
| `ram.py`, `scan_w.py`, `census_sum.py`, `widen_test.py` | RAM and widescreen research helpers |
| `keypost.ps1 -Keys F5,Down,Return` | Post key presses to the game window only |
| `wincap.ps1 -Out x.png` | Capture the game window only (PrintWindow). Never capture the desktop |

Fresh checkout order: `gen.sh` (or copy `generated/`), `bios.sh`,
`build.sh`, `deps.sh`.
