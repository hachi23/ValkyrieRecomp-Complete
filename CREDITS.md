# Credits

This repository is a personal fork. Most of the code in it was written by
other people. This page says whose work is whose.

## Original projects

| Project | Author | What it provides | Base used by this fork |
| --- | --- | --- | --- |
| [ValkyrieRecomp](https://github.com/Ed1z19/ValkyrieRecomp) | Ed1z19 | The Valkyrie Profile port: game configuration, symbols, seeds, branding, release workflow and setup packaging | `3894f4a` |
| [PSXRecomp](https://github.com/mstan/psxrecomp) | Matthew Stanley (mstan) and contributors | The recompiler and runtime: CPU translation, renderers (software, OpenGL, Vulkan), save states, rewind, fast-forward, crash report, mods | Ed1z19's fork at [`8c26d19`](https://github.com/Ed1z19/psxrecomp) |
| [recomp-ui](https://github.com/mstan/recomp-ui) | Matthew Stanley (mstan) | The Dear ImGui launcher | Ed1z19's fork at [`6ae46a2`](https://github.com/Ed1z19/recomp-ui) |

Libraries vendored inside `psxrecomp/`:

- **recomp-net** and **retcomm-rbengine**, by their contributors (MIT),
  in `psxrecomp/lib/`.
- **OpenBIOS** (from PCSX-Redux), **libchdr**, **TinyCC** and others, listed
  with their licenses in
  [psxrecomp/THIRD_PARTY_ATTRIBUTION.md](psxrecomp/THIRD_PARTY_ATTRIBUTION.md).
- **[rcheevos](https://github.com/RetroAchievements/rcheevos)** by the
  RetroAchievements team (MIT), added by this fork for achievement support
  and vendored in `psxrecomp/third_party/`.

## References

- **[DuckStation](https://github.com/stenzek/duckstation)**: its block-level
  handling of video-decoder (MDEC) memory transfers was the model for this
  fork's movie-decoding speedup. No DuckStation code was copied.
- **[psx-spx](https://psx-spx.consoledev.net/)**: the PlayStation hardware
  reference used to confirm that change is safe.

## This fork

Made by [hachi23](https://github.com/hachi23) in October 2026 by directing AI
coding agents. Everything this fork added or changed is listed in
[docs/CHANGES.md](docs/CHANGES.md).

## The game

*Valkyrie Profile* was developed by tri-Ace and published by Enix in 2000.
The game, its code and its assets belong to their rights holders. Nothing
from the game is included in this repository.
