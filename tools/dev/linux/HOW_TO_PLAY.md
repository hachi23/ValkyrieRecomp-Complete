# How to play Valkyrie Profile on Linux (ValkyrieRecomp)

This folder holds everything the game needs: the program, both discs, your
memory cards and save states, and the launcher. Keep the folder together. You
can move it anywhere, as long as everything inside moves with it.

## Unpack

Copy `ValkyrieRecomp-Linux.tar` to your Linux machine and unpack it:

    tar -xf ValkyrieRecomp-Linux.tar

Unpack it with `tar` on Linux rather than copying the folder through a Windows
drive, so the program keeps its "can run" permission.

## What your system needs

Any recent desktop Linux works. It needs:

- glibc 2.43 or newer. Check with `ldd --version`. CachyOS and other rolling
  distributions have it.
- curl, zlib and OpenGL libraries. On CachyOS / Arch: `sudo pacman -S --needed
  curl zlib libglvnd`. They are almost always installed already.
- For Vulkan, your graphics driver's Vulkan support. On AMD (CachyOS):
  `sudo pacman -S --needed vulkan-radeon`.

## Start the game

1. Run `./play.sh` from this folder (or double-click it in your file manager
   and choose "Run").
2. The launcher opens. Check that it says **Disc verified** under the cover.
3. Press **PLAY**.

A desktop shortcut should point at `play.sh`.

## Differences from the Windows version

- Settings start fresh. Pick your renderer, resolution and controller again in
  the launcher, and log in to RetroAchievements again under Settings.
- Your memory cards (`saves/card1.mcd`, `saves/card2.mcd`) are the same files
  as on Windows, so in-game saves carry over.
- Save states were made on Windows. They should load, but that is not tested;
  keep using in-game saves for anything important.
- Hotkeys are the same: F5 Quick menu, F7 save states, Shift+F6 change disc,
  Ctrl+C reinsert disc, Alt+Enter fullscreen, Tab fast-forward.

## If something goes wrong

- **Nothing happens when you run it.** Start it from a terminal with
  `./play.sh` and read the message. "GLIBC_2.43 not found" means your system
  is older than this build; ask for a build made on your machine
  (`tools/dev/build_linux.sh` in the source repo).
- **The launcher says the disc is missing.** Check that `disc/Disc1` and
  `disc/Disc2` still hold the `.cue` and `.bin` files.
- **Problems with Vulkan.** Choose OpenGL under Settings > Renderer.
- The newest files in `logs/` describe the last session; keep them when you
  report a problem.
