# Valkyrie Profile cheat catalog

The Disc 1 catalog contains USA codes attributed to hacker 12345 on
[GameHacking.org](https://gamehacking.org/game/90093?game=90093).
Every entry starts disabled and is marked untested. Published addresses are
source evidence, not evidence that a code works in this recomp or the undub.

Disabling a cheat stops future writes. It cannot undo inventory changes,
progress, or instructions already changed by a cheat. Safe mode suppresses
cheats for one run while preserving saved selections.

Disc 2 has no catalog yet. Disc 1 addresses must not be silently applied to
Disc 2. Its compatibility needs separate evidence.

Owner checks remain pending. Check each entry separately in its named area,
confirm its button combination, disable it, and reload a clean save before
checking another entry. Keep a clean memory-card backup outside the game.

## Adding your own cheats

`SLUS-01156.toml` is the one cheat list the game reads. Edit it from the
launcher's Assist Tools page instead of by hand:

- **Add to cheat list.** Paste codes into the box. One cheat, or a whole list
  copied from a website: a line without codes names the codes under it. The
  box checks every line as you type and names any code it cannot run.
- **Import file.** Adds the cheats from a RetroArch `.cht` file, a `[Name]`
  block file (PCSX, ePSXe, DuckStation), or a plain text file. Cheats whose
  codes are already in the list are skipped.
- **Replace all with file.** Saves the current list as `SLUS-01156.toml.bak`,
  then keeps only the file's cheats.
- **Delete.** Click twice to remove a cheat, bundled or yours.

A packaged build copies this starter list next to the game only when no list
is there yet, so rebuilding never overwrites your edits.
