# ValkyrieRecomp — private fork plan

Goal: a personal Valkyrie Profile PC build that runs on **Vulkan by default**
(AMD GPU), with **resolution/upscaling controls**, a **cheat system usable from
both the launcher and an in-game overlay**, and **crash logging good enough to
tell which cheat broke something**.

## Repos

| Repo | What lives there | Why we touch it |
|---|---|---|
| `hachi23/Valkyrie-recomp` | Game config (`game.toml`), branding, CI | Vulkan default, cheat file for VP |
| `hachi23/Psx-recomp-` (submodule) | Recompiler + runtime (`runtime/src/main.cpp`, renderers, savestates, crash report) | Cheat engine, in-game overlay, logging, Vulkan fixes |
| `hachi23/Recomp-ui` (submodule) | Dear ImGui launcher (`src/common/backends/imgui/launcher_imgui.cpp`) | Cheat list UI, ungating graphics options for Vulkan |

Copied from `Ed1z19/*` at ValkyrieRecomp `3894f4a`, psxrecomp `8c26d19c`,
recomp-ui `6ae46a2`. Keep `upstream` remotes pointing at `Ed1z19/*` and
`mstan/*` so fixes can be pulled in later.

## What already exists (do not rebuild these)

Found while surveying the code on 2026-10-05:

- **Vulkan backend** — `runtime/src/gpu_vk_renderer.c`, built by default when the
  Vulkan SDK (headers + `glslc`) is present; `release.yml` already installs it.
  Selected by `renderer = "vulkan"` (value `2`). Launcher only lists it when
  `game.toml` has `[video] offer_vulkan = true`. Status in
  `psxrecomp/docs/ENHANCEMENTS.md` §R2: renders gameplay at ~60 fps, FMV and
  16:9 done; **SSAA >1 unvalidated on Vulkan**; semi-transparent prims drawn
  one-per-draw (perf cost).
- **Resolution / quality settings** — `RecompLauncherSettings` already has
  `supersampling` (1–4×), `antialiasing` (MSAA), `texture_filter`
  (nearest/bilinear), `frame_interp` + `frame_interp_fps`, `screen_kind`
  (CRT filters). Some controls are gated to OpenGL only (`renderer == 1`).
- **Save states, rewind, fast-forward** — `savestate.c`, `psx_savestate_menu.c`,
  `psx_rewind.c`, bound under the launcher's "Assist Tools / Cheats" view.
- **HD texture packs** — `hd_texture_pack.cpp`.
- **Crash report** — `crash_trace.c` writes `psx_last_run_report.json` on
  SIGSEGV/SIGABRT/SEH/fail-fast. **Overwritten every run**, no history.
- **In-game menu library** — recomp-ui `src/recomp_runtime_ui.h` (bool/int/
  choice/action items, `graphics.resolution_scale` key) rendered via ImGui.
  psxrecomp does **not** use it yet at this pin.
- **Software-drawn overlays** — `host_osd.c` (toasts) and `psx_savestate_menu.c`
  draw with an 8×8 font into the frame, so they work on every renderer.

What does **not** exist: a cheat code engine, a cheat list, an in-game cheat
toggle, persistent logs.

---

## Phase 0 — Build and baseline (do first)

0. **Undubbed disc support.** The owner's discs are an **undubbed** USA image
   (Japanese voices, English text), not the retail Redump image. The
   generator checks disc digests against `[prepare_disc] known_md5 /
   known_sha1 / known_sizes` in `game.toml` and refuses anything else
   (`DiscVerifyError` in `psxrecomp/psxrecomp_cli.py`).
   - Run `psxrecomp_cli.py verify-disc` on each undubbed disc; the error
     prints its size, MD5 and SHA-1. **Append** them to the three lists
     (keep the retail entries; the lists are matched by position). Never
     use the skip-hash option as the fix.
   - Check the boot executable `SLUS_011.56` is byte-identical to retail. If
     it is, the existing function seeds (`seeds/ghidra_funcs.txt`) and
     overlays apply unchanged. If it differs, stop and report before going on.
   - Undub patches often move or resize voice files on the disc. Watch for
     missing or wrong voice clips, hangs during voiced scenes, and Disc 2
     loading problems during the baseline run, and note them in the
     learning log as undub-specific.
   - Keep the cue/bin file names in `game.toml` (`discs`, `[prepare_disc]`)
     matching the owner's actual files.
1. Build on Windows following `psxrecomp/docs/BUILDING.md` with the Vulkan SDK
   installed (`VULKAN_SDK` set). Confirm CMake prints that the Vulkan backend
   is enabled.
2. Run once on **OpenGL** and record a baseline: boot → title → first field →
   first battle → world map → an FMV → save to memory card → load.
3. Make 4–6 memory-card saves / save states at those checkpoints. Every later
   phase is tested against the same checkpoints.

Done when: OpenGL baseline plays through the checkpoints and a Vulkan-capable
build exists.

## Phase 1 — Vulkan by default

1. `game.toml`: `[video] renderer = "vulkan"` and `offer_vulkan = true`.
2. Walk every Phase 0 checkpoint on Vulkan, then repeat at SSAA 2× and 4×,
   at 4:3 and 16:9. Compare against the **software** renderer (the reference)
   using psxrecomp's frame-aligned capture tooling (`frameshot.py`, see
   ENHANCEMENTS.md R2) where something looks off.
3. Watch especially: battle spell effects (heavy semi-transparency), sprite
   seams when upscaled, world-map 3D, FMVs, loading a save state
   (`vk_renderer_restage_vram_after_savestate`), Disc 2 boot.
4. Fix bugs in `hachi23/Psx-recomp-`, then bump the submodule pointer.
5. Fallback: if Vulkan fails to initialise, the runtime already drops to
   OpenGL when Vulkan isn't compiled in — extend that to a **runtime** init
   failure (no Vulkan ICD / device lost) so the game still starts.

Done when: all checkpoints pass on Vulkan at 1×/2×/4× with no visual diff
worse than OpenGL's.

## Phase 2 — Graphics settings GUI

Launcher (recomp-ui, settings page):
1. Ungate the OpenGL-only controls for Vulkan where the Vulkan backend
   implements them: supersampling 1–4×, texture filter, MSAA (check
   `gpu_vk_renderer.c` support before exposing each; hide what VK can't do).
2. Label supersampling as **Internal resolution** with the resulting size
   (1× = 320×240 … 4× = 1280×960 native-ish).
3. Optional later: add an **xBR / smooth sprite filter** choice (shader-side;
   suits VP's 2D sprites better than bilinear).

In-game: expose Internal resolution and Texture filter in the overlay from
Phase 3 so they can change without restarting (check the backend handles a
scale change at runtime; if not, show "applies on restart").

Done when: every option shown actually changes the Vulkan output and persists
in `settings.toml`.

## Phase 3 — Cheats

### 3a. Engine (psxrecomp runtime, new `runtime/src/cheats.c` + `.h`)

- Format: GameShark/Action Replay codes. Support types
  `80` (16-bit write), `30` (8-bit write), `D0/D1/D2/D3` (16-bit conditionals),
  `E0/E1` (8-bit conditionals), `50` (serial repeat), `C0`/`D4`–`D6` if needed.
- Apply once per frame at vblank (hook next to `psx_vblank_clock.c`), only
  while **Assist Tools / Cheats** is enabled (existing `assist_tools` gate).
- Live toggle: enable/disable any cheat at any moment. On disable, stop
  writing; optionally restore the value captured just before first write
  (useful for constant-value cheats; document that game state changed while
  it was on cannot be fully undone).
- Cheat file per game: `cheats/SLUS-01156.toml` in this repo (+ `SLUS-01179`
  for Disc 2 if codes differ):
  ```toml
  [[cheat]]
  id = "max-hp"            # stable id used in logs and settings
  name = "Infinite HP (party)"
  codes = ["800XXXXX YYYY", "800XXXXX YYYY"]
  notes = "Source + tested area"
  ```
  Populate from existing Valkyrie Profile (USA) GameShark lists; mark each as
  tested/untested.
- Enabled set persists per game in `settings.toml` (list of ids).
- Save states: store the active cheat ids in the state's metadata; warn (OSD)
  when loading a state made with different cheats.
- Unit tests for the code parser and conditional logic (runtime has a test
  harness under `runtime/tests/`).

### 3b. Launcher GUI (recomp-ui)

- Extend `draw_assist_tools()` in `launcher_imgui.cpp`: a searchable list of
  cheats with checkboxes, notes tooltip, "Disable all", and a **Safe mode**
  toggle ("start with all cheats off this run").
- Pass the list host→launcher via the existing GameInfo / settings plumbing
  (additive fields, like `assist_tools`).

### 3c. In-game overlay

Recommended: **software-drawn menu** in the style of `psx_savestate_menu.c`
(draws into the frame, so it works identically on Vulkan/OpenGL/software):
hotkey + pad combo opens it, game pauses while open, lists cheats with
on/off, plus Internal resolution / Texture filter / Save state / Load state.

Alternative (nicer looking, more work): integrate recomp-ui's
`recomp_runtime_ui` (ImGui) — requires an ImGui Vulkan backend hooked into
the Vulkan present path in `gpu_vk_renderer.c` plus the GL path. Only do this
after 3c-software works.

Every toggle shows an OSD toast (`host_osd.c`) and writes a log event (Phase 4).

Done when: a cheat can be toggled from the launcher and mid-game, survives a
restart, and Safe mode boots clean.

## Phase 4 — Logging and crash diagnostics

Note: `psxrecomp/CLAUDE.md` §3 says "No log files. Ever." **This fork
deliberately overrides that** for one low-volume event log. Keep it
event-level (not per-frame, not per-instruction).

1. **Session log** `logs/session-YYYYMMDD-HHMMSS.log`, keep last 10:
   build id, GPU/driver (Vulkan device name + driver version), renderer and
   all graphics settings, disc serial, cheats file hash, then timestamped
   events with **guest frame number**: cheat on/off (id), save/load state,
   renderer fallback, overlay captures/self-heal, warnings. Flush after each
   line so a crash never loses the tail.
2. **Crash history**: after `crash_trace.c` writes its report, copy it to
   `logs/crashes/crash-<timestamp>.json` (keep last 20) instead of only the
   overwritten `psx_last_run_report.json`.
3. **Add to the crash report**: active cheat ids, cheat toggles in the last
   ~600 frames, renderer + settings, last loaded save state, session log path.
4. **On next launch after a crash**: launcher shows "Last run crashed" with
   the cheats that were active and a one-click Safe mode.
5. Debug workflow when a cheat is suspected: Safe mode → re-enable cheats in
   halves (bisect) → the session logs show which id was on at the crash frame.

Done when: forcing a crash (debug action) produces a timestamped crash file
that names the active cheats, and the next launch offers Safe mode.

## Phase 5 — Release builds

`release.yml` already builds Windows/Linux/macOS with Vulkan. On a private
repo, GitHub Actions minutes are limited on free accounts (2,000/month), so
build locally day to day and run CI only for tagged releases. Never upload
disc images or BIOS files (already in `.gitignore`).

---

# Enhancements: the definitive Valkyrie Profile

Two kinds of work below:
- **Runtime-level**: works for any PS1 game; no knowledge of Valkyrie
  Profile's code needed.
- **Game-level**: needs reverse engineering (RE) of Valkyrie Profile itself —
  finding where it keeps values in memory and which functions do what. There
  is no VP decomp, so this is discovered from scratch. Record every finding
  (address, meaning, how it was found) in `docs/VP_MEMORY_MAP.md` so later
  features reuse it.

Rule for all game-level changes (borrowed from Ship of Harkinian): every
change to how the original game behaves is a **toggle, off by default**,
listed in the launcher and the in-game overlay. Default settings = the
original game.

## Phase 6 — Quick wins (runtime-level)

1. **Turn on existing features** and expose them in the launcher + overlay,
   checking each works with Vulkan: fast loading (`turbo_loads`), high-quality
   audio (`spu_hq`), CRT filters (`screen_kind`), skip FMVs (`auto_skip_fmv`),
   HD texture pack loading (`hd_texture_pack.cpp`) and the mod loader
   (`mod_runtime.cpp`). Decide sensible defaults for VP.
2. **Sprite filter**: add an xBR-style smoothing filter for 2D sprites and
   backgrounds as a texture-filter choice (Phase 2 item 3), on Vulkan first.
   Apply it per texture before compositing, not over the finished frame.
   Add a separate **de-dither** filter that blends the checkerboard
   dithering baked into VP's art. Both are opt-in toggles, off by default
   (owner decision 2026-10-05). Compare against nearest/bilinear on field,
   battle and menu screens.
2b. **HD texture packs** (later): first search for an existing Valkyrie
   Profile pack online. `hd_texture_pack.cpp` can load packs but is not
   wired to any renderer, and no texture-dump tool exists yet.
3. **RetroAchievements**: integrate the `rcheevos` library. The PS1 set
   (retroachievements.org game 11249) reads PS1 memory addresses, and the
   recomp keeps the PS1 memory layout, so the existing set should work
   unchanged. Needs: login in the launcher, achievement pop-ups via the
   overlay, hardcore mode disabling cheats / save states / rewind /
   fast-forward (RetroAchievements rules). Verify a few early achievements
   unlock in real play.

Phase 6 findings (2026-10-05): fast loading, CD speed, PGXP and bezels are
already bundled Mods (off by default); High-quality SPU and the CRT "Screen
model" are already launcher settings. Skip FMVs is mod-owned on PSX, and the
framework's generic skipper does not work for VP: during the title-menu
Opening Movie the MDEC decode count never moves and no XA stream is active,
so the detector never fires, even though pressing START does end the movie.
A VP Skip Movies mod needs a game-level "movie playing" signal (Phase 7 RE).
When adding a game mod: put `PRELOADED_MODS_DIR` before
`CODEGEN_SETUP_SOURCES` in `psxrecomp_add_game_runtime`, or the multi-value
list swallows it and silently drops the setup-host source.

## Phase 7 — Game-level quality of life

Starts with RE groundwork shared by every item: map the memory addresses and
functions listed under each item into `docs/VP_MEMORY_MAP.md`. Cheat codes
from Phase 3 are a good starting map (they already point at known values).

0. **Skip movies**: DONE 2026-10-06 without RAM reverse engineering. The
   Phase 6 note above was wrong about MDEC: the anime movies do use it (no XA).
   The title menu's "Opening Movie" is a live-rendered story scene, not a
   video, which is why no decoding showed there. `valkyrie.skip-fmv` enables
   the runtime skipper with `fmv_skip_no_xa` plus the new
   `fmv_skip_require_depth24`, so MDEC clips drawn into 15-bit battle and
   dungeon scenes never trigger it. `tests/agent/skip_fmv_live.py` checks the
   movie checkpoint and the title scene with the mod off and on.
1. **Text speed**: option for faster / instant dialogue text.
   Find the text printing routine and its per-character delay.
2. **Battle speed**: speed up battle animations and effects (e.g. 1.5×/2×),
   and optionally allow skipping long special-attack animations after the
   first time. Valkyrie Profile's combos depend on button timing, so
   confirm combos still work at each speed.
3. **A-ending tracker**: DROPPED by the owner 2026-10-06. The Seal value is
   already shown at the bottom of Valkyrie's status screen in the game, so
   an overlay adds nothing. (Starts at 80; A ending needs 37 or less in
   Chapter 7. Not found in 0x801F5E00-0x801F6400 at the world-map tutorial.)
4. **Widescreen**: DROPPED by the owner 2026-10-06 in favour of a simple
   **Stretch to fill** option (DuckStation's "Stretch To Fill": the original
   4:3 frame scaled to the whole window, no widescreen hack). `game.toml`
   `[video] offer_stretch = true` makes the launcher's Aspect ratio choices
   4:3 (Original) / Stretch to fill; the choice is `[video] stretch` in
   `settings.toml`. Vulkan and OpenGL only (software stays 4:3).
   Why true widescreen was dropped: VP's fields are pure 2D (no GTE), so the
   squash mode only pillarboxes. Native-wide mode widens the picture and the
   right edge fills mid-room, but a ~50 px left strip is never drawn and room
   ends show past the authored art. Raising the 42 hard-coded `320` compares
   and loads in the loaded field code (0x80038F50-0x800B4180) changed almost
   nothing (4 extra prims), so the left cull is a different test. Finishing it
   means per-mode reverse engineering (field, dungeon, battle).
5. **Modern button prompts**: show Xbox or PlayStation button icons that
   match the connected controller in menus and tutorial text. Requires
   finding where the game draws button glyphs and replacing those graphics.

## Phase 8 — (dropped) Japanese voices toggle

Not needed: the owner plays from an **undubbed** disc image (Japanese voices,
English text), so Japanese voices come from the disc itself. Support for that
image is handled in Phase 0 step 0.

## Phase 9 — Optional fixes menu

A "Fixes & tweaks" section in the launcher and overlay, every item a toggle
off by default, each with a one-line description and source (where the bug
or complaint is documented). Populate as bugs and annoyances are found
during play-testing; each entry needs a written before/after test.

---

## Order and rough size

| Phase | Size | Depends on |
|---|---|---|
| 0 Build + baseline | small | — |
| 1 Vulkan default | small config, unknown bug-fix tail | 0 |
| 2 Graphics GUI | small–medium | 1 |
| 3a Cheat engine | medium | 0 |
| 3b Launcher cheats | small–medium | 3a |
| 3c In-game overlay | medium | 3a |
| 4 Logging | small–medium | 3a (for cheat fields) |
| 5 Release builds | small | 1 |
| 6 Quick wins | small–medium | 1, 3c (overlay) |
| 7 Game-level QoL | medium–large (mostly RE) | 3a, 3c |
| 9 Fixes menu | ongoing | 3c |

3a and 4 can start in parallel with 1. Out of scope by choice: randomizer,
music replacement packs.
