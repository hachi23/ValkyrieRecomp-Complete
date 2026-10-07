# What this fork changed

This page separates what this fork added from what it inherited. Credits for
the original work are in [CREDITS.md](../CREDITS.md).

## Where the work happened

The fork started on 2026-10-04 from Ed1z19's ValkyrieRecomp `3894f4a`,
PSXRecomp `8c26d19` and recomp-ui `6ae46a2`. Work was done step by step in
three separate repositories, then combined here on 2026-10-06 in one import
commit (`1a3729d`), so this repository's history starts there.

| Folder here | Developed in | Final branch and commit |
| --- | --- | --- |
| repo root | `hachi23/Valkyrie-recomp` | `feat/phase-7-text-speed` `761af1e` |
| `psxrecomp/` | `hachi23/Psx-recomp-` (18 commits) | `feat/stretch-to-fill` `5928390` |
| `recomp-ui/` | `hachi23/Recomp-ui` (8 commits) | `feat/diorama-theme` `3a667a9` |

Commits after the import are in this repository's own history.

## Performance

Measured on the development laptop (Radeon RX 560X, Linux). Each result
compares the same fixed workload from save states, with the old and new
builds run alternately. Full method and raw data:
[PERFORMANCE_FINDINGS.md](PERFORMANCE_FINDINGS.md).

| Change | Scene | Before | After |
| --- | --- | ---: | ---: |
| Interpreter hands overlay code to precompiled native code | World map | ~32 fps | 51 fps |
| Debug display recorder made opt-in | First field | 36 fps | 60 fps |
| | World map | 27 fps | ~32 fps |
| | Peak memory | 590 MB | 528 MB |
| CD-ROM interrupt fix, plus precompiling the movie decoder routine | Opening movie | 21.7 fps | 28.3 fps |
| Video-decoder (MDEC) transfers land in whole blocks | Opening movie | 28.3 fps | 42.0 fps |
| | Full movie, wall time | 163 s | 113 s |
| Consecutive see-through sprites share one Vulkan render pass | Petal cutscene | 32 fps | 56–60 fps |

What each change was:

- **Overlay hand-over.** Parts of the game's code are loaded from disc while
  it plays. They ran in the slow interpreter even when a precompiled copy
  existed, because the interpreter only checked at the start of a function.
  It now also checks when a call returns and when overlay code jumps. Every
  hand-over still verifies the code in memory matches what was compiled.
- **Debug display recorder.** With debug tools on, every frame copied 1 MB of
  video memory back from the GPU for a diagnostic ring buffer. It is now off
  unless `PSX_DISPLAY_RING=1`. Release builds without debug tools never
  included it, so this mainly let automated testing run at full speed.
- **CD-ROM interrupt.** A delivered but unacknowledged CD interrupt was still
  reported as a pending event, which forced about 1.1 million full hardware
  catch-ups per emulated second during movies.
- **MDEC block transfers.** Movie data moved one word at a time, each with a
  hardware catch-up. It now lands per block (32 words for this game) at the
  cycle its last word is due. Total timing and the completion interrupt are
  unchanged. Basis: psx-spx documents that the CPU cannot observe word order
  inside a block, and DuckStation transfers MDEC data per block. Sampled
  frames were pixel-identical. `PSX_MDEC_BLOCKS=0` restores the old path.
- **Render-pass batching.** The petal scene started and ended a separate GPU
  render pass for each of about 700 see-through sprites per frame. Consecutive
  sprites now share one pass, still drawn in the same order.

**Rejected:** CPU-cached Vulkan readback memory. It improved the first field
by 39% but slowed the world map by 23% and raised driver memory 6%, breaking
the limit set before testing (no other metric may worsen by more than 5%). It
was reverted, and the patch is archived locally.

## Reliability and diagnostics

| Feature | Inherited | Added by this fork |
| --- | --- | --- |
| Vulkan renderer | Existed, opt-in | Default renderer; steps down Vulkan → OpenGL → software at runtime, cleaning up between attempts, with the reason logged. Verified by hiding the Vulkan driver, then also limiting OpenGL |
| Crash report | One report, overwritten every run | Crash history (last 20) with active settings, cheats and last save state |
| Session logs | None | Per-run log of GPU, driver, settings, disc, cheats and renderer fallbacks (last 10 kept) |
| Unexpected exit | Not detected | Marker file; the launcher opens with a notice and a Safe mode option |
| Freeze detection | Watchdog with 30–130 MB freeze dumps | False alarms at the boot logo and in paused menus fixed; only the newest 3 dumps kept |
| Release packaging | Setup-host release workflow by Ed1z19 | Verified the release zip contains no disc, Sony BIOS, saves or generated code; fixed a window-size bug it exposed; added a Linux build |

## Tests and code health

- 8 of 47 runtime tests had been failing unnoticed because nothing ran them.
  Causes: Windows text encoding and line endings (2), expectations left stale
  by deliberate upstream changes (3), code lines that had been renamed or
  rewrapped (2), and missing test setup (1). All 47 now pass.
- `tools/dev/check.sh` runs the build, all tests, a keymap test, settings
  round trips, a docs drift check and a launcher screenshot in one command.
- Settings and hotkeys now come from one table each instead of hand-copied
  lists. A settings round-trip test caught two launcher choices being
  silently changed (a disabled memory card, player 2's deadzone); both fixed.

## Player features

- GameShark cheat engine applied at vertical blank; launcher editor, paste
  checking, import from RetroArch, DuckStation and PCSX formats; in-game
  cheats menu; cheats recorded with save states.
- RetroAchievements through rcheevos.
- Smooth (xBR-style) and De-dither texture filters on Vulkan.
- Mid-session disc swap and a Quick Menu with rebindable hotkeys.
- Stretch to fill, window fitting, fullscreen fixes, 16x and larger windows.
- Launcher text size and the Diorama theme.

## Not verified

From the measurement records: full guest-state equality after the engine
changes, movie audio, battles, long sessions, and Disc 2 performance. The
Windows release workflow was not run from this fork.
