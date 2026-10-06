# Handoff, 2026-10-06 (evening, Windows play PC)

This is the **all-in-one repo** for the ValkyrieRecomp fork
(`hachi23/ValkyrieRecomp-Complete`). It replaces the old three-repo setup.
Start every session here.

Read `AGENTS.md`, `CLAUDE.md`, this file and `docs/CLEANUP_PLAN.md` first.
`LEARNING.md` holds the owner-facing lessons. `PLAN.md` holds the long-term
phases of the port.

## How to work in this repo

- **Poteto mode, no agents.** Use the project skill
  `.claude/skills/poteto-solo/SKILL.md`. It loads pstack poteto-mode from
  `~/.claude/skills/poteto-mode/` (installed on this PC, read by path because
  it is not model-invocable) and maps every "spawn an agent" step to a step
  you do yourself. Never call the Agent tool here.
- **Owner rules (AGENTS.md).** Teach in plain language. Add a dated lesson to
  `LEARNING.md` after each step. Keep answers short. Ask before committing or
  pushing. The owner prefers quick wins over long reverse-engineering.
- **Next work.** Execute `docs/CLEANUP_PLAN.md`, starting at Phase 0.

## What this repo is made of

Built on 2026-10-06 from these pushed commits (history stays in the old repos):

| Folder | Came from | Branch | Commit |
|---|---|---|---|
| repo root | `hachi23/Valkyrie-recomp` | `feat/phase-7-text-speed` | `761af1e` |
| `psxrecomp/` | `hachi23/Psx-recomp-` | `feat/stretch-to-fill` | `59283906` |
| `recomp-ui/` | `hachi23/Recomp-ui` | `feat/diorama-theme` | `3a667a9` |
| `psxrecomp/lib/recomp-net` | `TechnicallyComputers/recomp-net` | | `c10cac1` |
| `psxrecomp/lib/retcomm-rbengine` | `TechnicallyComputers/retcomm-rbengine` | | `ebd94a4` |

There are no submodules any more. `psxrecomp/` and `recomp-ui/` are plain
folders, so one commit can change the game, the framework and the launcher
together. `AGENTS.md` still describes the old submodule workflow in its
"Working with submodules" section. Treat that section as history; update it
when convenient.

Changes made here after the import (first commit):

- `tools/dev/`: the helper scripts, formerly the git-ignored
  `analysis/agent-tools/`, with paths made relative (CLEANUP_PLAN Phase 0
  item 2, done).
- `CLAUDE.md`, `.claude/skills/poteto-solo/SKILL.md`, this handoff.
- **Launcher text size** (owner request). Settings > SYSTEM > Launcher text
  size cycles Auto / 100 / 125 / 150 / 175 / 200%, saved as
  `config.ini [Launcher] UiScale` (`auto` or a percent; env
  `LNG_UI_SCALE` overrides for scripts). Cause of the small launcher: the
  game sets `permonitorv2` DPI awareness, so Windows does not enlarge the
  window and SDL reports pixel density 1, while the launcher never applied
  the display content scale. Now `g_ui_scale` scales `px()`, fonts and the
  ImGui style, and the window is sized to 1100x880 times the scale, capped to
  fit the screen. Also fixed `begin_panel()` double-scaling measured widths
  and the dashboard breakpoint. Measured: Auto picks 155% on this 2560x1440
  175% screen (window 1710x1368, every page fits); clicking the row
  switched to 100% live and saved it.

## Machine and local files

- Windows 11, Ryzen 7 7800X3D, Radeon RX 9070 XT, 2560x1440 OLED. Windows
  display scale is 175% on this PC (Measured with GetDpiForSystem). The owner
  mentions 150%.
- Checkout: `D:\Emulation\Recomps\Valkyrie\ValkyrieRecomp-Complete`.
- Local only (git-ignored, recreate on a new machine):
  - `disc/Disc1`, `disc/Disc2`: junctions to
    `D:\Emulation\Recomps\Valkyrie\Valkyrie Profile (Undub)\Disc 1|2`, plus
    `disc/SLUS_011.56` and `disc/SYSTEM.CNF`. Never delete the Undub folder.
  - `generated/` (game C), `psxrecomp/generated/` (OpenBIOS C) and
    `psxrecomp/runtime/include/overlay_codegen_hash.h`. Copied from the old
    checkout. `tools/dev/gen.sh` and `tools/dev/bios.sh` regenerate them.
  - `saves/` (memory cards and save states), `build-win/` (built from
    scratch here on 2026-10-06).
- Old checkout `D:\Emulation\Recomps\Valkyrie\Valkyrie-recomp` still exists
  and is fully pushed. Do not work there.
- Play package for the owner: `D:\Emulation\Recomps\Valkyrie\ValkyrieRecomp-Play`
  (exe, DLLs, discs, saves, `Play.bat`, `HOW_TO_PLAY.md`). Refresh it from
  `build-win/` after user-visible changes: copy the exe and any changed
  assets, keep its relative-path `settings.toml`, and update the guide.

## Build, run, test

Scripts are in `tools/dev/` (see its README). Run them through PowerShell:
`& C:\msys64\usr\bin\bash.exe -l tools/dev/build.sh`. Running them from the
Bash tool fails in ccache because `USERPROFILE` is missing there.

- Build: `tools/dev/build.sh`. It also copies the MinGW DLLs next to the exe
  (`psxrecomp/tools/bundle_mingw_dlls.sh`), so a fresh `build-win/` starts.
- Run for agents: `build-win\ValkyrieRecomp.exe --no-launcher --debug-port 4398
  --memcard-dir <repo>\saves --renderer vulkan --disc "<repo>\disc\Disc1\...cue"`
  with `PSX_BIOS_HLE=0`. Debug commands: `savestate op=save|load slot=N`,
  `disc_swap`, `turbo enabled=1`, `screenshot_file`, `gpu_state`,
  `read_ram`/`write_ram`, `input_route_*`.
- Launcher screenshots: `LNG_SCRIPT="wait:60;view:settings;wait:20;shot:<png>;quit"`
  with `--launcher`. `click:x,y` (window pixels), `key:<name>` and
  `size:WxH` also work. Set `LNG_UI_SCALE=100` when a script clicks fixed
  coordinates. Settings save on PLAY. Hotkeys and text size write
  `config.ini` at once; delete test `config.ini` files afterwards.
- Window capture: `tools/dev/wincap.ps1` (PrintWindow). Never capture the
  desktop. Keys: `tools/dev/keypost.ps1` (cannot carry Shift into SDL).
- Save states: slot 3 (file `slot03`) Valhalla balcony, slot 5 world map,
  slot 7 in the menu (file `slot06`) balcony. Slots 1 and 2 caught the title
  demo; overwrite them.
- Runtime tests: `python psxrecomp/runtime/tests/<name>.py`. All 47 pass
  (the overlay test needs MinGW `gcc` on PATH). Before committing run
  `& C:\msys64\usr\bin\bash.exe -l tools/dev/check.sh` (build, tests, TCP
  docs, launcher smoke). Phase 0 of `docs/CLEANUP_PLAN.md` is done.

## State at handoff (2026-10-06 night, Phase 1 done)

### Pick up here

Branch `cleanup/phase-1`, **uncommitted** work, Phase 1 complete (builds,
`check.sh` says CHECK OK, 47/47 tests). `main` = `9fd28f6` (owner bug fixes + Phase 0),
pushed. Commit Phase 1 on this branch only after the owner says so.

Phase 1 of `docs/CLEANUP_PLAN.md`, item by item:

| # | Item | State | Evidence |
|---|---|---|---|
| 1 | Relative paths | Done, verified | `load_user_settings` anchors bios/disc/memcard paths to the settings file's folder; `save_user_settings` writes paths inside it relative (`config_loader.cpp`). Before: started from another folder, blank `card1/2.mcd` were created in `<start>/../saves`. After: a moved copy of the play folder started from `C:\Windows\Temp` loaded disc + RA, and PLAY rewrote an absolute disc path to `disc/...` |
| 2 | Freeze dumps into `logs/` | Done, verified | `freeze_heartbeat.c` writes dumps and `psx_freeze_heartbeat.json` under `session_log_dir()` (new accessor). `psx_last_run_report.json` still goes to the current folder (already archived in `logs/crashes/`) |
| 3 | DLL bundling | Done, verified | `bundle_mingw_dlls.sh` stopped at `Secur32.dll`; added common OS DLLs to the list and a System32 fallback on Windows. `build.sh` now runs it; `tools/dev/deps.sh` deleted. Bare exe: 0xC0000135 before, exit 0 after |
| 4 | Vulkan menu scale | Done earlier (`4d18101`) | |
| 5 | Ctrl+C to `[KeyMap] ReinsertDisc` | Done, verified | Quick Menu REINSERT DISC showed "Disc reinserted", logged `disc reinsert`, game kept running. Launcher HOTKEYS shows Reinsert disc = Ctrl+C. The Ctrl+C key itself was not pressed (keypost cannot carry modifiers) |
| 6 | PlayStation button names | Done, verified | Launcher Controller page: Cross, Triangle, Left stick up. HOTKEYS: Triangle + Select, Select + R3 |
| 7 | Tell RA about disc changes | Done, verified | `ra_change_disc()` in `ra_host.{h,cpp}` (no-op until the set is loaded), called from `disc_swap_next()`. Logged in as hachi11, `disc_swap` to 2 and back logged `retroachievements: disc change accepted` |
| 8 | Bound `assist_default_*_bind` copy; stale `game.toml` comment | Done | Copy bounded by `assist_binding_count` in `launcher_model.c` (NDS passes 2 entries, old code read 8). `game.toml` comment was already fixed at import |

Remaining before commit: the owner's go. Then refresh the play package if
not done (see Next steps), commit Phase 1 on `cleanup/phase-1`, merge.

Test copy: the scratchpad `ratest` folder is a copy of the play package
with the new exe and RA token. Nothing in the repo depends on it.

### Owner decisions this session

- Fullscreen bug and achievement pop-up style: owner said ignore for now.
- Merging to `main` is approved for finished work; ask before each commit.

### Local test state

- `build-win/settings.toml` was restored to its original (it still points
  at the old `Valkyrie-recomp` checkout; that is finding D, harmless now
  that paths load relative).
- Play package `settings.toml` holds the owner's RA token (user hachi11).
  Never commit it.
- Scratch copies live under the session scratchpad (`MovedInstall`,
  `fresh`); nothing in the repo depends on them.

### Verified game state

Working on Vulkan at 60 fps: title, New Game, Valhalla, world map, save
states, Quick Menu, disc swap, Stretch to fill, launcher, RetroAchievements
login (game 11249, 174 achievements), 16x internal resolution.

Not verified: battle, a real Disc 2 load from a late save, controller
presses (no pad connected), fullscreen symptom the owner reported (could not
reproduce; owner deferred it).

## Next steps

1. Owner go for the Phase 1 commit; the owner still needs to press Ctrl+C
   in game and try the pad shortcuts.
2. Finding J (freeze dumps of 30 to 130 MB in normal play). Quick win.
3. Phase 2 single source of truth (settings table, hotkey catalog). Item 5
   showed finding B again: one hotkey touched 6 files in 2 projects.
4. Phase 3 file splits.
5. Update the "Working with submodules" section of `AGENTS.md`.
6. Findings I1/I2 in `docs/CLEANUP_PLAN.md`.
