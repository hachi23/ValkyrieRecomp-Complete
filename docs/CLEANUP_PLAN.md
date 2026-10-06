# Cleanup and architecture plan (2026-10-06)

An audit of the three repos (game, psxrecomp, recomp-ui) for weak seams: places
that work today only because several hand-kept copies happen to agree, or
because nothing checks them. Each finding names the evidence. The plan orders
the fixes so that every phase leaves the build working and checkable.

Labels used below. **Measured** means I ran it this session. **Read** means I
read the code at that line. **Guess** means not yet proven.

## Fixed during this audit

- Keyboard column of the Controller page's shortcut table did nothing for PSX.
  The launcher saved `assist_key_bind`, and psxrecomp never read it (Read: no
  reader anywhere in `psxrecomp/`). It now edits the real `[KeyMap]` key
  through the new `GameInfo.assist_binding_hotkeys` map.
- Change disc was a hard-coded Shift+F6 outside the keymap. It is now
  `[KeyMap] DiscSwap` (default Shift+F6) plus a controller binding
  (`[hotkeys] disc_swap_pad`). Measured: rebinding to F10 swapped discs in game.
- Quick menu's controller button was a hard-coded constant. It is now
  `[hotkeys] quick_menu_pad` (default Select + Triangle) and editable.
- Settings > HOTKEYS shows Keyboard and Controller side by side, and lists
  Quick menu, Change disc, Fast-forward toggle and Scanlines, which existed in
  the runtime but had no launcher row.
- Save-state disc scope at startup used the settings' disc index, not the
  mounted disc (fixed earlier today, measured).

## Findings

### A. Settings are copied by hand in eight places

`psxrecomp/runtime/src/main.cpp` moves every launcher setting between four
shapes (globals, `UserSettings us`, `UserSettings seed`, `RecompLauncherCSettings
ls`) in eight separate blocks (Read: the pad hotkeys alone appear at the
`us ->`, `-> seed`, `seed -> ls`, `ls -> seed`, `seed ->`, `-> ls`, `ls -> us`
and `ls ->` sites). Each block restates the defaults. Adding one setting means
eight edits that must agree, plus parse and write in `config_loader.cpp`.
Risk: a missed site silently drops a setting on one launch path only. This is
the biggest duct-tape seam in the codebase.

### B. Two hotkey catalogs in two repos, kept in sync by hand

The runtime names actions in `host_keymap.c` (`action_for_key`, defaults in
`apply_defaults`). The launcher names the same actions in
`recomp-ui/src/common/launcher_binds.c` (`kHotkeyKey`, `kHotkeyDef`) and
`launcher_model.c` (`kHotkeyNames`). A typo in either spelling breaks a hotkey
with no error (Read). Today's change had to touch all four tables.

### C. Tests check source text, not behaviour, and 8 already fail

19 of 47 `psxrecomp/runtime/tests/*.py` files read `main.cpp` as text and
assert that exact lines exist (Measured). 8 of the 47 fail on the committed
code today (Measured, same 8 at `HEAD` and with today's changes):
`test_dirty_text_continuation_guards`, `test_interpreter_perf_guards`,
`test_launcher_vulkan_option`, `test_mod_owned_display_controls`,
`test_overlay_pair_dedup_runtime`, `test_release_zip`,
`test_rewind_toggle_combo`, `test_runtime_perf_diag_guards`. Nobody noticed,
so nothing runs them. A reformat breaks them and a real bug passes them.

### D. Paths depend on the current folder and get pinned as absolute

`normalize_disc_path_for_launch` resolves relative paths with
`fs::absolute`, which uses the process's current folder, not the exe's
folder (Read, `main.cpp` near line 2395). The launcher then writes absolute
disc and memory-card paths into `settings.toml` (Read). Moving the install, or
starting it from a shortcut with another "Start in" folder, points the game at
the old saves or at nothing. The play package works around this with
`Play.bat` and a hand-made relative `settings.toml`.

### E. Generated docs and files drift silently

- `docs/TCP_COMMANDS.md` was 6 commands behind the code before today's
  regeneration (Measured: 311 to 317). `gen_tcp_commands.py --check` exists
  but nothing runs it.
- `game.toml` line 13 still says mid-session disc swap "is not implemented".
- The native overlay build (`generated/overlays/overlays_static.c`) can only
  be made with the Linux recipe in `docs/PERFORMANCE_FINDINGS.md`
  (`/usr/bin/gcc`). This Windows build has none. Disc-loaded overlay code runs
  in the slower interpreter. It still holds 60 fps on this PC (Measured
  earlier today), so this is headroom, not a bug.

### F. Fragile build and run steps

- MinGW DLLs are copied by hand. `bundle_mingw_dlls.sh` stops at
  `Secur32.dll`, and a fresh `build-win` exits with 0xC0000135 until someone
  repeats the copy (handoff).
- The helper scripts that make testing possible (`analysis/agent-tools/`)
  are git-ignored and live on this PC only.
- Freeze dumps (`psx_freeze_dump_*.json`) land in whatever folder the game was
  started from. The repo root has 3 and `build-win/` has 13 (Measured).

### G. Small seams that will bite later

- `recomp-ui/src/common/launcher_model.c` copies a fixed 8 entries from the
  game's `assist_default_*_bind` arrays, whatever their real length (Read).
  A game that passes shorter arrays reads past them. psxrecomp passes none,
  so this game is safe today.
- Vulkan draws the in-game menus 1:1 (`vk_osd_blit` in `gpu_vk_renderer.c`),
  so they look tiny on large windows. OpenGL scales them (Measured).
- Ctrl+C is a hidden "reinsert disc" panic button (commit `adba58b6`). It is
  useful, but it is not rebindable, not listed in HOTKEYS, and logs in
  Spanish.
- Controller labels use SDL names ("y", "r3") instead of PlayStation names
  (Triangle, R3) (Measured in the launcher).
- RetroAchievements is not told about a disc change
  (`rc_client_begin_change_media` is never called).
- `launcher_imgui.cpp` keeps the theme pointer `volatile` to dodge a GCC 15.2
  miscompile. The cause was never found (Read, the comment above `g_th`). It
  may be undefined behaviour elsewhere (Guess).

### H. Three files hold most of the program

`main.cpp` is 15,820 lines with 85 file-level globals, `debug_server.c` is
14,706 lines, and `launcher_imgui.cpp` is 10,344 lines (Measured). Settings,
hotkeys, menus, disc handling and launcher bridging all share one file and
one set of globals, which is why finding A exists.

## The plan

Each phase ends with something you can run to prove it. Phases 0 and 1 are
small and safe. Phases 2 and 3 are the real cleanup.

### Phase 0. Make breakage visible (about one session)

1. Fix or delete the 8 failing tests. Replace text checks with behaviour
   checks where a debug-server command can show the behaviour (hotkeys,
   save states and disc swap all have one).
   Check: all runtime tests pass.
2. Commit the helper scripts from `analysis/agent-tools/` to `tools/dev/`, so
   any machine can build, run and test.
3. One script, `tools/dev/check.sh`, that builds, runs the runtime tests,
   runs `gen_tcp_commands.py --check`, and runs the launcher screenshot
   smoke test. Run it before every commit.

### Phase 1. Quick seam fixes (one or two sessions)

1. Resolve relative disc, memory-card and BIOS paths against the exe's
   folder, and write them back relative when they are inside it (finding D).
   Check: move the play folder, launch from a shortcut elsewhere, saves load.
2. Write freeze dumps into `logs/` (finding F).
3. Make the DLL bundling script skip system DLLs, and call it from the build
   (finding F). Check: delete `build-win`, rebuild, the exe starts.
4. Scale the Vulkan menu overlay like OpenGL does (finding G).
5. Turn the Ctrl+C panic button into `[KeyMap] ReinsertDisc` and a Quick menu
   row (finding G).
6. PlayStation button names in controller labels (finding G).
7. Tell RetroAchievements about disc changes (finding G).
8. Bound the `assist_default_*_bind` copy by `assist_binding_count`
   (finding G). Fix the stale `game.toml` comment.

### Phase 2. One source of truth (two or three sessions)

1. Settings table. One table in psxrecomp lists each setting once: its
   global, its `settings.toml` key, its default, its launcher field. The
   eight copy blocks become four loops over it (finding A). Start with the
   six pad hotkeys, prove it, then move the rest.
   Check: a test that writes a `settings.toml`, round-trips it through the
   launcher path and the in-game launcher path, and compares every field.
2. Hotkey catalog. One list of hotkey actions (name, `[KeyMap]` key,
   default) that both `host_keymap.c` and recomp-ui use, generated or shared
   by header (finding B).

### Phase 3. Split the large files (two or three sessions, move-only)

Move code without changing it, one file per area, each move its own commit
with a build and smoke test.

- `main.cpp` into `settings_bridge.cpp` (launcher round-trip),
  `hotkeys.cpp`, `quick_menu.cpp`, `disc_swap.cpp`, `boot.cpp`.
- `debug_server.c` into one file per command group, registered from a table.
- `launcher_imgui.cpp` into one file per panel (display, audio, hotkeys,
  controller, cheats, netplay, mods).

### Phase 4. Performance and deep debt (as wanted)

1. Make the native overlay build work on Windows (finding E), then measure
   the gain before keeping it.
2. Find the real cause behind the `volatile g_th` workaround (finding G).
3. The later art options from the handoff (screen shaders, HD textures).

## Not done, and why

- The settings and file splits (Phases 2 and 3) are large moves across code
  owned by the shared framework. They need the Phase 0 safety net first, so
  they were planned, not started.
- The controller side of the new hotkeys was not pressed on a real pad. No
  controller was connected. It uses the same matcher as the existing
  controller shortcuts, and the bindings are saved and shown correctly
  (Measured in the launcher).
