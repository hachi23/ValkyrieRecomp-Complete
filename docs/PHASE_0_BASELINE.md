# Phase 0 baseline record

Recorded on 2026-10-04. Phase 0 is in progress.

## Disc fingerprints

These fingerprints describe each undub BIN data track from the owner's local discs.
The existing retail Disc 1 entry remains in `game.toml`.
The size, MD5, SHA-1, and CRC32 lists have matching positions for retail Disc 1, undub Disc 1, undub Disc 2, and the supplied retail Disc 2.
The CLI disc verifier uses MD5 or SHA-1 membership and does not consume `known_crc32`.

| Image | Size in bytes | MD5 | SHA-1 | CRC32 |
| --- | --- | --- | --- | --- |
| Undub Disc 1 | 730448880 | `2d39a2817fd76dd98e11047434f770e2` | `4a5f95b45a0ed401a67164f2126230a6c508f606` | `fdee286a` |
| Undub Disc 2 | 747352704 | `50860f81b2808c8e0e25707e5bc515c4` | `3ae00a34f25c4f8745cac7c10f040b2c87a04c0c` | `2ed8728f` |
| Supplied retail Disc 2 | 747352704 | `19f36bd625e676ea5d74db612d26eb6c` | `7cc65766b46273b4ee166269170ecbaa433908fd` | `c2132829` |

The configured CUE paths are `disc/Disc1/Valkyrie Profile (Undub) (Disc 1).cue` and `disc/Disc2/Valkyrie Profile (Undub) (Disc 2).cue`.
Disc files stay local in the ignored `disc/` directory.
The initial hash rejection was expected because the config accepted only the retail fingerprint.
Adding the measured undub fingerprints preserves hash checking.

## Boot executable comparison

The extracted boot programs from both undub discs are byte-for-byte identical to each other.
Their measured header values match the existing game configuration.

| Property | Measured value |
| --- | --- |
| File size | 131072 bytes |
| SHA-256 | `78ad0f390a1aec6b4528c4115a566336a643b0263c3e3f1f59ceafefb7792358` |
| Load address | `0x80010000` |
| Entry address | `0x80010008` |
| Text size | `0x1f800` |

Retail executable comparison passed. The owner supplied both retail discs.
The supplied retail Disc 1 matched the existing recognized disc fingerprint.
The initial config omitted retail Disc 2; its measured fingerprint was added alongside the undub entries.
Each extracted retail boot program is byte-for-byte identical to its corresponding undub boot program, with zero differing bytes.
All four boot programs have the SHA-256 recorded above.
The retail comparison supports using the existing function seeds and overlays unchanged. Their runtime behavior still needs gameplay validation.

## Build and gameplay status

The OpenGL build was launched and reached the title screen. Two captured images show distinct opening-movie frames. Sound has not been verified by listening.
Windows PowerShell runs verified GCC `15.2.0`, CMake `4.3.1`, and Ninja `1.13.2`.
Vulkan SDK `1.4.363.0` is installed at `C:\VulkanSDK\1.4.363.0`. Its `glslc` shader compiler runs.
The SDK installer SHA was verified before installation.
The installed GPU is an AMD Radeon RX 9070 XT with driver version `32.0.32015.2008`.
The Windows Release build succeeded as `build-release/ValkyrieRecomp.exe`.
The real Vulkan renderer and its shaders compiled. `PSX_ENABLE_VULKAN=ON`, `GLSLC_EXE` points to the installed SDK, and `PSX_STATIC_RUNTIME=ON`.
Vulkan gameplay validation belongs to Phase 1. This build result does not prove gameplay compatibility.
OpenGL remains the configured renderer for the baseline.

| OpenGL checkpoint | Status |
| --- | --- |
| Boot | Passed on Disc 1 with bundled OpenBIOS, BIOS HLE disabled |
| Title screen | Passed, captured `analysis/phase0-boot-debug.png` |
| First field | Untested |
| First battle | Untested |
| World map | Untested |
| Full-motion video | Opening movie displayed distinct frames in two captures, sound unverified |
| Save to memory card | Untested |
| Load from memory card | Untested |
| Japanese voice playback in voiced scenes | Untested |
| Disc 2 loading | Separate OpenGL run reached the tri-Ace publisher logo; gameplay and disc swapping untested |

Six repeatable saves or save states are planned at the title screen, first field, first battle, world map, a full-motion video checkpoint, and a memory-card save location.
A save state captures the running console state. A memory-card save uses the game's own save system.
The memory-card checkpoint must include closing and reopening the game before loading the save.
One opening-movie save state was created in slot 0. The save and load operations both completed successfully according to `savestate_status`, and the movie continued afterward.
This checks save states, not the game's memory-card save/load. Five additional checkpoint saves remain to be created.
The local baseline build uses `PSX_DEBUG_TOOLS=ON` for inspection and screenshot capture. `PSX_HAVE_VULKAN=1` appears in the compiled target definitions; Vulkan gameplay is untested.

Windows detected an Xbox 360-compatible controller. Local settings assign Player 1 to gamepad in digital mode; actual controller button response remains unconfirmed.

The Vulkan-capable Windows build is complete. Phase 0 remains incomplete until the remaining OpenGL checkpoints and repeatable saves pass. Work is moving to a separate CachyOS system; see [the migration handoff](CACHYOS_HANDOFF.md).

## CachyOS verification (2026-10-05)

Both supplied undub discs pass `verify-disc` without bypassing fingerprints. The original and undub boot executables for both discs share SHA-256 `78ad0f390a1aec6b4528c4115a566336a643b0263c3e3f1f59ceafefb7792358`.

The Linux Release build succeeds in `build-linux` with `PSX_DEBUG_TOOLS=ON` and `PSX_ENABLE_VULKAN=ON`. The Vulkan backend and shaders compile. OpenGL remains the baseline renderer. Vulkan gameplay remains untested.

Disc 1 reaches the title with `PSX_BIOS_HLE=0` and bundled OpenBIOS. Title captures are local ignored files `analysis/linux-first-frame.png` and `analysis/linux-title-checkpoint.png`. Slot 1 is `saves/openbios/state_80010008_disc1_slot01.pst`. Both save and restore completed with matching successful `savestate_status` receipts. Gameplay checkpoints and memory-card behavior remain unverified.

SDL detects the GameSir-Dongle controller, and the runtime opens it for Player 1 in digital mode. Physical button response remains unconfirmed.

Ghidra 12.1.2 and Java 21 are installed. The GhidraMCP 7.0.0 extension builds against the installed Ghidra. The localhost backend at port 8089 opens the persistent ignored `ghidra/projects/ValkyrieProfile.gpr` project. The imported payload uses `MIPS:LE:32:default` with image base `0x80010000`. A decompilation request at entry `0x80010008` succeeds with instruction warnings. The Codex MCP entry is registered, and the user service `ghidra-recomp.service` starts at login.

All 50 pstack skills, including Poteto Mode, are installed from the handoff-pinned revision `124f622bcaeac490e7e9dac6af83f3ef9611d554`. Reload Codex to discover newly installed skills and the registered MCP entry. The bridge can already be queried through its local MCP client.

## Checkpoint runner verification (2026-10-05)

`tests/agent/run.py` reuses the framework debug client. `tests/agent/scenarios.json` records title slot 1 and leaves first-field, first-battle, and world-map checkpoints unrecorded. Its outputs remain under ignored `analysis/agent/`. The runner never writes or overwrites saves.

Three live title replays completed, including a final replay after review changes. The first capture was visually inspected and shows the title screen. Load completion receipts, queued-input completion, capture signature, chunks, decompression, dimensions, and cleanup are checked. Captures occur during live execution and do not prove an exact guest frame or gameplay correctness.

A SIGTERM interruption during a held-button route returned failure and acknowledged cleanup. An independent status query confirmed controller override `-1` and route inactive. An unrecorded battle scenario failed before connection even with port 1. A recorded title scenario against an unavailable server returned failure and recorded the failed cleanup attempt.

Scripted input reached the New Game difficulty screen and selected Normal. A separate local introduction state in slot 2 was saved and restored with successful completion receipts. The introduction appeared in captures, but full playback and sound remain unverified. Slot 2 is exploratory and is not registered as a completed gameplay checkpoint.

Independent spec and standards reviews found no blocking issues in the runner. The reviews used the same model family available in this session. Physical controller input and all remaining gameplay checkpoints are still pending. Phase 1 has not started.

A separate Linux Disc 2 OpenGL instance reached its title menu. Its debug server used port 4372 and its writable state used ignored `analysis/disc2-cards`, separate from Disc 1. The inspected capture is `analysis/linux-disc2-boot.png`. This verifies Disc 2 boot only. Disc 2 gameplay and in-session disc swapping remain untested.

After the Disc 1 introduction state was restored, later captures remained in the castle scene. Image comparison found changed pixels between captures, so this observation does not establish a freeze. The first playable field has not been reached or recorded. Local CD-ROM and movie-decoder status evidence is in `analysis/setup-evidence/`; no runtime fix is justified by this observation alone.

## Keyboard field baseline (2026-10-05)

Real keyboard events are generated with ydotool through `/dev/uinput`, with the Wayland game window focused through a transient KWin script. X down produces pad `0xBFFF`; release produces `0xFFFF`. Debug override remains `-1` throughout. The recorded status is `analysis/setup-evidence/keyboard-x-probe.json`.

Arrow movement and story interaction passed on the Valhalla balcony. Walking left reached Frei; keyboard dialogue input progressed through Odin's chamber into the human-world scene. This supersedes the earlier observation that the first playable field had not been reached. No runtime code fix was needed.

The `first_field` checkpoint uses slot 3, `saves/openbios/state_80010008_disc1_slot03.pst`, at the balcony departure dialogue. Save and restore receipts succeeded and the restored scene was inspected. The existing runner replayed it and produced inspected `analysis/agent/20261004T212619Z_first_field_s84yighe/first_field.png`. Field rendering and keyboard interaction are verified; the first battle and world map remain pending.

A ten-second stereo audio capture was linked directly from the game's PipeWire output ports into `analysis/phase0-freya-audio.wav`. It contains nonzero audio. No microphone or desktop-wide monitor was recorded. Audio input is unsupported by the current model, so Japanese language, voice timing, and complete movie audio are not marked passed.

The running kernel is `7.1.5-1-cachyos`; installed kernel files are newer. Keyboard automation initially failed because uinput was unavailable. The matching signed uinput module was extracted from the cached `linux-cachyos-7.1.5-1` package and loaded without changing installed kernel files. ydotool now runs as the user using existing device ACL access.

## World-map tutorial checkpoint (2026-10-05)

The story reached Midgard's 3D world-map tutorial with Freya. Slot 5 was saved, restored, and inspected. Both completion receipts succeeded, recorded in `analysis/setup-evidence/world-map-state-receipts.json`. `world_map` now replays that local checkpoint; its inspected capture is `analysis/agent/20261004T213231Z_world_map_ff8yeghs/world_map.png`.

This supersedes the pending world-map scene check above. Terrain, sky, and flying character sprites render in the tutorial scene. Later chapter map features remain untested. The on-screen tutorial instructed pressing START for spiritual concentration; the corresponding Enter key was sent through the real keyboard path. Battle and memory-card restart checks remain pending.
