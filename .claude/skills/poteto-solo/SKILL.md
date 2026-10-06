---
name: poteto-solo
description: "Poteto mode for this repo, run without subagents. Use for every non-trivial task here (features, bug fixes, refactors, cleanup phases, investigations, plans): it maps each poteto-mode step that would spawn an agent to a step you do yourself."
---

# Poteto mode, solo route

The owner wants the pstack **poteto-mode** discipline, but **no subagents**.
Never call the Agent tool in this repo. This file adapts poteto-mode to that.

## Load the real skill first

poteto-mode is installed in `~/.claude/skills/` but marked
`disable-model-invocation`, so it is not in your skill list. Read it by path:

- `~/.claude/skills/poteto-mode/SKILL.md` (Non-negotiables, Principles,
  Writing the reply, Playbooks)
- the matching playbook in `~/.claude/skills/poteto-mode/playbooks/`
- every principle leaf you apply, `~/.claude/skills/principle-*/SKILL.md`
- routed skills you use, for example `how`, `architect`, `blast-radius`,
  `unslop`, `technical-writing`

Everything in them applies except the parts this file replaces.

## The solo mapping

poteto-mode's own Harness note already allows this: "If your harness has no
subagent tool, do each delegated step yourself, one after another." Apply it
as follows.

| poteto-mode says | Do this instead |
|---|---|
| `how` explorers and explainer | Explore yourself. Grep first, then read only the line ranges you need (`offset`/`limit`). Write the Overview / Key Concepts / How It Works / Where Things Live / Gotchas output. |
| `architect` Phase B (arena runners) | Sketch at least two structurally different designs yourself, each with its data shape and signatures. Compare them in a table (interface depth, reader load, red flags). Pick one and say why. |
| `arena` / `swarm` lanes | Run the candidates or scenarios one after another yourself. Each lane is one scenario you execute with `tools/dev/` and record (log line, screenshot, debug-server reply). |
| Feature step 4 "delegate code-writing" | Write the code yourself. Then do a separate cold review of your own diff before committing: re-read `git diff`, run the **blast-radius** checklist, and fix what it finds. That second pass is the review separation. |
| `interrogate` / `why` / `reflect` | Write the strongest argument against your choice, then check it against the code. Keep the result in the reply. |
| Explore in subagents (multi-phase plan step 3) | Explore yourself; keep file pointers and test commands, not dumps. |
| `show-me-your-work` decision trail | Keep it in the reply, or in `docs/` for long multi-phase runs. |
| Guard the Context Window by routing bulk to subagents | Guard it by reading narrowly, summarizing into `docs/`, and never pasting whole large files (`main.cpp` 15.8k lines, `debug_server.c` 14.7k, `launcher_imgui.cpp` 10.3k). |
| `check-plan.mjs` | Run `node ~/.claude/skills/poteto-mode/scripts/check-plan.mjs <plan.md>` if `node` exists; otherwise check the plan against the skeleton by hand. |
| PR / babysit / shipping playbooks | This repo works on branches pushed to `origin`. Commit and push only when the owner says so (see AGENTS.md). |

## Verification in this repo (Prove It Works)

"It compiles" is not proof. Use the real surface:

- Build: `C:\msys64\usr\bin\bash.exe -l tools/dev/build.sh` (log in
  `tools/dev/build.log`).
- Runtime tests: `python psxrecomp/runtime/tests/<test>.py`. 8 fail on the
  baseline already; see `docs/CLEANUP_PLAN.md` finding C. Report new failures
  only against that list.
- Launcher: `LNG_SCRIPT="wait:40;view:settings;wait:15;shot:<png>;quit"` with
  `build-win\ValkyrieRecomp.exe --launcher`, then look at the PNG.
- Game: `--no-launcher --debug-port 4398`, `python tools/dev/dbg.py <cmd>`,
  `tools/dev/keypost.ps1` for keys, `tools/dev/wincap.ps1` for window shots.
  Never capture the desktop.
- A controller is not always connected. Say so when a pad path is untested.

## House rules that stay on top

- AGENTS.md teaching rule: plain language, a dated lesson in `LEARNING.md`
  after each step, short answers.
- Name the principles that shaped each decision in the reply (poteto
  Non-negotiables), citing only leaves you read this session.
- No long dashes, no mid-sentence colons in replies (Writing the reply).
