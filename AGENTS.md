# Agent instructions (ValkyrieRecomp private fork)

Read `PLAN.md` first. Work one phase at a time, in order, unless told otherwise.

## Teaching rule (always applies)

The owner is learning how games, consoles and recompilation work through this
project. He is a gamer, not a programmer: he can read a little Python but does
not write code, and he wants to understand how things work, not learn to code.
Teach from scratch.

After **every phase** (and after any significant step inside a phase):

1. **Stop and explain** in the chat, in plain language:
   - what was done and why it was needed
   - how that part of the game, the PS1 or the recomp works, using gaming
     comparisons where they help
   - what you tested, and what still needs him to test in the real game
   No code in the explanation unless he asks for it. Define every technical
   term the first time it appears (e.g. "renderer: the part that turns the
   game's drawing commands into pictures on screen").
2. **Add a lesson to `LEARNING.md`** (append; never rewrite earlier lessons):
   a dated heading, the plain-language explanation, and a short "Words
   learned" list. This file is his growing guide to how everything works.
3. **Invite questions and wait.** End with "Any questions before the next
   phase?" Do not start the next phase until he says to continue. Answer
   questions at the same plain level, and add anything important from the
   answers to that phase's lesson.

When something breaks, explain what the failure reveals about how the game
or hardware works before fixing it.

## Layout

- This repo: game config and packaging for Valkyrie Profile (USA, SLUS-01156 /
  SLUS-01179). Two submodules, both private forks owned by `hachi23`:
  - `psxrecomp/` — recompiler + runtime. Most code changes go here.
  - `recomp-ui/` — Dear ImGui launcher.
- `psxrecomp/CLAUDE.md` and `psxrecomp/CONTRIBUTING.md` describe framework
  rules. Follow them, **except**: this fork allows the single low-volume
  session/event log and crash-history files described in PLAN.md Phase 4.

## Working with submodules

1. Commit and push the change inside `psxrecomp/` or `recomp-ui/` first
   (branch per feature, e.g. `feat/cheats-engine`).
2. Then commit the updated submodule pointer in this repo.
3. Never leave this repo pointing at an unpushed submodule commit.

## Build

See `README.md` here and `psxrecomp/docs/BUILDING.md`. The Vulkan SDK must be
installed (`VULKAN_SDK` set) or the Vulkan backend is silently compiled out.

## Rules

- Never commit disc images, BIOS files, saves, `generated/`, or build output.
- The software renderer is the correctness reference. When a Vulkan frame
  looks wrong, compare against software at the same guest frame before
  changing renderer code.
- Prefer extending existing systems (assist-tools gate, `host_osd.c`,
  `psx_savestate_menu.c`, `crash_trace.c`, `RecompLauncherSettings`) over new
  parallel ones. Add launcher struct fields additively at the end.
- Every new feature needs a way to verify it: a unit test under
  `psxrecomp/runtime/tests/` for logic (cheat parser, conditionals), and a
  written manual check against the PLAN.md Phase 0 checkpoints for anything
  visual.
- Report what you verified and what you could not (you cannot run the game
  without the user's disc).
