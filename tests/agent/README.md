# Replay a Phase 0 checkpoint

Run a recorded local save through the game's native debug server. The runner writes a screenshot and command receipts under an ignored, unique `analysis/agent/` directory. It never creates or overwrites save states.

1. Start the debug-enabled OpenGL game with Undub Disc 1 and the project's save directory. Keep other debug clients inactive during replay.
2. Leave the physical controller untouched. Controller input resumes after queued input ends.
3. List available checkpoints.

   ```sh
   python tests/agent/run.py list
   ```

4. Replay the verified title checkpoint.

   ```sh
   python tests/agent/run.py run title_idle
   ```

5. Open `title.png` in the printed directory. Inspect the title scene and read `evidence.json` for the load receipt, route completion, capture dimensions, and cleanup result.

Use `--port PORT` or `--timeout SECONDS` after the scenario name to change the server port or completion deadline. Each network query also has the existing debug client's ten-second socket timeout. The completion deadline does not interrupt a query already in progress. The screenshot path must be accessible to the running game on this computer.

`title` uses slot 1, and `first_field` uses slot 3 at the Valhalla balcony departure dialogue. Both were saved, restored, and inspected on Linux OpenGL. Replay the field with `python tests/agent/run.py run first_field`. `world_map` uses slot 5 in Freya's Midgard map tutorial and replays with `python tests/agent/run.py run world_map`. The runner refuses missing files and unrecorded checkpoints before contacting the runtime. For example, `python tests/agent/run.py run first_battle` fails until a real battle checkpoint has been created, restored, inspected, and recorded in `scenarios.json`.

A successful run proves the runtime completed a save-state load, consumed queued input, and wrote a valid PNG. Inspect the screenshot to judge the scene. The runner cannot prove which disc is mounted or which save directory the runtime uses. Launch with the known configuration. The runtime checks state compatibility during load.

Input spans contain a positive frame count and an active-low PS1 digital button word. `65535` releases all buttons. Every route ends with neutral input. The runner uses native route completion rather than removed pause or step commands. Its capture happens during live execution, so the recorded frame interval does not identify an exact guest frame.

Ctrl+C and SIGTERM attempt `clear_input` through a fresh connection before writing the evidence file. Cleanup failures make the run fail. SIGKILL, a disconnected game, or a process crash can prevent cleanup. Finite input routes bound the duration of a held button. Use one runner per runtime because save requests and input routes share runtime state.

Phase 0 remains incomplete. Battle, complete FMV playback and audio, undub voices, memory-card load after restart, and Disc 2 gameplay need separate checks. The world-map checkpoint verifies the tutorial scene; later chapter map features remain untested. `screenshot_hires` refuses 24-bit FMV scanout. The runner reports that failure and does not treat it as a successful movie check. Keep game media, BIOS images, saves, and captures out of Git.
