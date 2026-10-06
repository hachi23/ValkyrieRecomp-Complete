# Windows to CachyOS handoff

Recorded 2026-10-04 at the owner's request. Stop Windows work here and resume Phase 0 on the separate CachyOS system. Phase 0 is incomplete; Phase 1 has not started.

## Work completed

- Read the plan, agent instructions, and framework instructions across the three repositories. Installed all 50 pstack skills from `backnotprop/pstack` at commit `124f622bcaeac490e7e9dac6af83f3ef9611d554`, including Poteto Mode, and used them for this work. These skills are installed on the old system; they will need installing or copying to the new system.
- Cloned the project recursively onto branch `feat/phase-0-undub`. Framework pin: `8c26d19c3700a64f24845fee2a452f47007e91f7`; UI pin: `6ae46a2632fef50856f568fd35f7e318eb0fe35c`. No submodule source changes.
- Measured both undub discs and added their accepted fingerprints to `game.toml`, retaining retail Disc 1 and adding the supplied retail Disc 2 fingerprint. Both undub discs pass the verifier without bypassing hash checks.
- Compared the extracted boot programs from both undub discs and both supplied USA discs. All four are byte-identical, with zero differing bytes. Their SHA-256 is `78ad0f390a1aec6b4528c4115a566336a643b0263c3e3f1f59ceafefb7792358`. Existing function seeds remain unchanged.
- Installed the official Windows Vulkan SDK and built the translation tools, generated game source, and Windows Release game successfully. Vulkan shaders and the actual Vulkan backend compiled. The output is `build-release/ValkyrieRecomp.exe`.
- Fixed the Windows portable CMake certificate setup so dependency downloads succeed with certificate verification enabled.
- Ran Disc 1 with OpenGL and bundled OpenBIOS, with BIOS HLE disabled. Captured the title screen and distinct opening-movie frames.
- Saved and restored an opening-movie save state in slot 0. Both operations reported success and the movie continued afterward.
- Booted Disc 2 separately to the tri-Ace publisher logo. This only verifies early boot, not Disc 2 gameplay or disc swapping.
- Detected a connected Xbox 360-compatible controller through Windows XInput. Assigned Player 1 to gamepad in local `build-release/settings.toml` and restarted the game. Actual button response has not been confirmed by the owner.
- Recorded measured evidence in `docs/PHASE_0_BASELINE.md` and appended explanations to `LEARNING.md`.

## Files and transfer

Old project folder: `/mnt/d/Emulation/Recomps/Valkyrie/Valkyrie-recomp` (Windows `D:\Emulation\Recomps\Valkyrie\Valkyrie-recomp`).

The owner requested publishing the handoff and completed configuration/documentation work to branch `feat/phase-0-undub` in `hachi23/Valkyrie-recomp`. On CachyOS, clone that branch recursively to obtain `game.toml`, `LEARNING.md`, `docs/PHASE_0_BASELINE.md`, and this handoff. These changes do not include disc images, saves, screenshots, or build output. No PR or merge to the default branch is part of this handoff.

Transfer the owner's undub disc images separately. Their old source folder is `D:\Emulation\Recomps\Valkyrie\Valkyrie Profile (Undub)` with `Disc 1` and `Disc 2` subfolders. The project's `disc/Disc1` and `disc/Disc2` are Windows junctions, not independent disc copies; recreate these paths with real files or Linux symlinks on CachyOS. The relative CUE paths expected by `game.toml` are listed in the baseline record.

If retaining evidence, copy ignored `analysis/` screenshots. If retaining the movie checkpoint, copy ignored `saves/`, including `saves/openbios/state_80010008_disc1_slot00.pst`. Save-state compatibility on the Linux build is untested. `card1.mcd` and `card2.mcd` were created, but no in-game memory-card save has been verified. Keep discs, saves, BIOS files, generated output, and build output out of Git.

## Resume on CachyOS

1. Read `PLAN.md`, `AGENTS.md`, this handoff, and the baseline record. Preserve the existing local changes and inspect repository/submodule status.
2. Set up the Linux dependencies using `psxrecomp/docs/BUILDING.md`. Build into fresh Linux build directories; Windows CMake caches and executables cannot be reused as native Linux builds. Regenerate local output using the transferred, verified discs as needed. Confirm Vulkan headers and `glslc` are found and the real Vulkan backend is enabled.
3. Keep OpenGL as the baseline renderer. The existing Windows Vulkan build satisfies the original Windows build milestone, but the new Linux environment needs its own build and runtime verification.
4. Check controller detection and mapping through SDL on Linux. The Windows XInput result does not prove Linux controller support. The local assignment used `p1_device = "gamepad"`, `p1_mode = "digital"`, and `p2_device = "none"`; recreate through the supported settings flow and verify actual button response.
5. Continue the missing OpenGL checks: first field, first battle, world map, full movie/audio, Japanese voice timing, in-game memory-card save and load after restarting, and Disc 2 loading/gameplay. Create the remaining repeatable checkpoints; only one movie state currently exists.
6. Update the baseline and append learning notes as results arrive. Do not mark Phase 0 complete until its gameplay checks and 4–6 checkpoint saves are verified. Explain the results and wait for the owner's continuation before Phase 1.

No Vulkan gameplay, upscaling settings, cheats, crash-history feature, or packaging changes have been implemented or verified. OpenGL remains configured in `game.toml`.
