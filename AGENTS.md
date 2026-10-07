# Agent instructions (ValkyrieRecomp fork)

Read `PLAN.md` and `docs/CLEANUP_PLAN.md` first. Work one phase at a time, in
order, unless told otherwise.

## Roles

The **project lead** (repository owner) sets goals, scope and acceptance
criteria, decides between options, tests results in the game, and approves
every phase before the next one starts. **Agents** investigate, implement,
test and document under those criteria.

## Working agreement (always applies)

After **every phase**, and after any significant step inside a phase:

1. **Report in plain language** so the lead can make an informed decision
   without reading the code:
   - what was done and why it was needed
   - how the relevant part of the game, the PS1 hardware or the recompiler
     works, and which trade-offs were considered
   - what was verified, and what still needs testing in the real game
   Define each technical term the first time it appears. Include code only
   when asked.
2. **Record the decision in `LEARNING.md`** (append; never rewrite earlier
   entries): a dated heading, the plain-language explanation and a short
   "Words learned" glossary. This file is the lead's private decision log:
   it is git-ignored and must never be committed here. Its backup lives on
   the `study-notes` branch of the private `hachi23/Valkyrie-recomp` repo.
3. **Wait for approval.** End with "Any questions before the next phase?"
   Do not start the next phase until the lead says to continue. Add anything
   important from the discussion to that phase's entry.
4. **Ask before committing or pushing.**

When something breaks, explain what the failure reveals about the game or
the hardware before fixing it. Prefer quick, measurable wins over long
reverse-engineering unless the lead asks for it.

## Layout

- This repo: game configuration and packaging for Valkyrie Profile (USA,
  SLUS-01156 / SLUS-01179).
  - `psxrecomp/`: recompiler and runtime. Most code changes go here.
  - `recomp-ui/`: Dear ImGui launcher.
- `psxrecomp/CLAUDE.md` and `psxrecomp/CONTRIBUTING.md` describe framework
  rules. Follow them, **except**: this fork allows the single low-volume
  session/event log and crash-history files described in PLAN.md Phase 4.

## One repo, no submodules

Since 2026-10-06 `psxrecomp/` and `recomp-ui/` are plain folders in this
repo, so one commit can change the game, the framework and the launcher
together. The earlier step-by-step history is in `hachi23/Valkyrie-recomp`,
`hachi23/Psx-recomp-` and `hachi23/Recomp-ui`. Record user-visible changes
in `docs/CHANGES.md`.

## Build

See `README.md` and `tools/dev/README.md`. On a fresh checkout: place the
discs where `game.toml` expects them, then run `tools/dev/gen.sh`,
`tools/dev/bios.sh` and `tools/dev/build.sh`. Run `tools/dev/check.sh`
before every commit. The Vulkan SDK must be installed (`VULKAN_SDK` set) or
the Vulkan backend is silently compiled out.

## Rules

- Never commit disc images, BIOS files, saves, `generated/`, build output,
  or machine-specific paths.
- The software renderer is the correctness reference. When a Vulkan frame
  looks wrong, compare against software at the same guest frame before
  changing renderer code.
- Measure performance changes with alternating before/after runs and limits
  set in advance (see `docs/PERFORMANCE_FINDINGS.md`). Reject changes that
  break a limit, and record them.
- Prefer extending existing systems (assist-tools gate, `host_osd.c`,
  `psx_savestate_menu.c`, `crash_trace.c`, `RecompLauncherSettings`) over new
  parallel ones. Add launcher struct fields additively at the end.
- Every new feature needs a way to verify it: a unit test under
  `psxrecomp/runtime/tests/` for logic (cheat parser, conditionals), and a
  written manual check against the PLAN.md Phase 0 checkpoints for anything
  visual.
- Report what you verified and what you could not (agents cannot run the
  game without the lead's disc).
