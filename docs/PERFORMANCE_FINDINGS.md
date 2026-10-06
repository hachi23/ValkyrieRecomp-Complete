# Low-FPS investigation, 2026-10-05

## What changed

Investigated the low animation rate in the isolated `Valkyrie-recomp-perf`
worktree, then built and tested one Vulkan readback candidate. The candidate
was **rejected and reverted**. No runtime optimization or multicore change is
retained. The original executable and settings were restored and verified.
The main checkout, its build, and its saves were not changed.

The owner's later request to investigate and optimize FPS expanded the earlier
Step 1-only task. The isolation, build, alternating-trial, regression-check,
and retention rules in `PERFORMANCE_STEPS.md` were retained.

The renderer is Vulkan on the RX 560X. Every accepted trial and each of the
three filter captures logged
`vulkan device AMD Radeon RX Graphics (RADV POLARIS11)`.

There are two distinct CPU bottlenecks:

- **Movie playback:** a confirmed 30-second profile remained in 320x240,
  24-bit video mode throughout. Completed decode commands increased from
  1519 to 1710. The interpreter's instruction executor consumed 23.27% of
  CPU samples itself, and its dispatcher consumed another 9.21%.
  Device servicing consumed 3.77%, interrupt checks 3.57%, and DMA event
  scheduling and DMA advancement each consumed 2.78%. These are self costs;
  nested call costs must not be added to them. About 99% of samples were on
  the main execution thread. The image decoder was not a dominant hotspot.
- **First field:** approximately 43.5% of samples were AVX memory loads
  inside the GPU-to-CPU VRAM copy. The full readback path consumed about
  46.7%. The debug display recorder requests current pixels, causing a full
  1 MiB readback repeatedly. The allocation selected coherent, CPU-visible
  memory without requesting CPU caching.

The compiled overlay system is disabled in the game configuration.
Live diagnostics confirmed `active=0`, `registered=0`, `dispatch_native=0`,
and automatic compilation `configured=0`, with its capture gate disabled.
An overlay is code loaded from the disc during play. Without compiled overlay
images, that code runs through the instruction interpreter. This is an
identified missing acceleration path, not proof that enabling a flag alone
will solve the movie problem. The exact hot guest routines still need to be
captured, compiled, and checked against the faithful interpreter.

The GPU already draws the game. Low utilization during the movie is consistent
with a CPU bottleneck. Independent decoding could run on a worker, but the
profile does not justify that as the first fix. Splitting the dependent PS1
instruction stream across CPU cores would not preserve execution order.

The candidate separated upload and readback buffer cache entries, requested
CPU-cached coherent memory for readbacks with a coherent fallback, and kept
the old memory selection selectable through `PSX_VK_CACHED_READBACK=0`.
It also supplied the required transfer-destination usage and a transfer-to-host
memory barrier. These correctness issues were archived with the reverted patch.
[Khronos describes cached host memory](https://docs.vulkan.org/spec/latest/chapters/memory.html),
[readback synchronization](https://docs.vulkan.org/guide/latest/synchronization_examples.html),
and [the required destination-buffer usage](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdCopyImageToBuffer.html).

## The numbers

One executable was used with cached allocation forced off for A and on for B.
Both paths included the transfer-usage and synchronization corrections, so this
comparison isolates cached allocation rather than measuring the complete patch
against the original executable. A logged memory type 2 with flags `0x6`;
B logged type 5 with flags `0xe`, confirming CPU caching was exercised.

Run order was A1 B1 A2 B2 A3 B3. The workload restored an isolated movie
checkpoint in slot 10, first field in slot 3, and world map in slot 5.
Each scene warmed for 60 guest frames. Timed work was 120 movie frames,
600 field frames, and 240 map frames, with a small polling overshoot.
No compiler or linker processes were allowed during sampling. Renderer,
settings, audio, build options, and the empty overlay inventory were identical.
Power settings were unchanged; clocks and thermals were not logged per trial.

The field's median present interval was the readback experiment's declared
primary metric before the campaign. The confirmed movie profile had ruled out
readback as the main movie cost. Video rate remained a secondary metric.

| Run | Field median ms | Field presents/s | Movie decoded images/s | Map median ms | Map GTT peak KiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 | 27.451 | 36.336 | 6.005 | 16.796 | 123548 |
| B1 | 16.661 | 60.020 | 6.002 | 34.649 | 133116 |
| A2 | 27.398 | 36.412 | 6.148 | 39.628 | 124764 |
| B2 | 16.661 | 60.020 | 6.207 | 48.740 | 132172 |
| A3 | 26.078 | 38.253 | 6.195 | 39.824 | 131116 |
| B3 | 17.076 | 58.283 | 6.024 | 52.530 | 129996 |

| Metric | A minimum | B minimum | Minimum change | A median | B median | Median change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Field median interval, lower better | 26.078 ms | 16.661 ms | -36.11% | 27.398 ms | 16.661 ms | -39.19% |
| Movie decoded images/s, higher better | 6.005 | 6.002 | -0.05% | 6.148 | 6.024 | -2.02% |
| Map median interval, lower better | 16.796 ms | 34.649 ms | +106.29% | 39.628 ms | 48.740 ms | +22.99% |
| Map GTT peak, lower better | 123548 KiB | 129996 KiB | +5.22% | 124764 KiB | 132172 KiB | +5.94% |

The median of each run's mean field throughput improved from 36.41 to
60.02 presents/s. Map mean throughput improved from 26.53 to 30.60 presents/s,
but its median interval worsened. Map intervals are uneven, so mean FPS and
median interval describe different behavior. That does not override the
explicit rule that no other measured number may worsen by more than 5%.

Median startup was 5.613 s for A and 5.612 s for B. Median process memory peak
was 588440 KiB for A and 591176 KiB for B, a 0.46% increase. No process swap
was observed. Driver GTT is system memory accounted by the GPU driver; it must
not simply be added to resident memory because mappings may overlap.

Scene-load receipts were polled at 200 ms intervals using the existing helper.
Raw medians were A/B: movie 215.9/65.6 ms, field 211.9/206.8 ms,
map 55.7/221.8 ms. This polling quantization makes those short load comparisons
unreliable. They are recorded, not claimed as real load-speed changes. No extra
campaign was run to chase a result. Map pacing and GTT already fail the gate.

**Decision: REJECT.** The field exceeds the 10% improvement threshold, but map
median interval worsens 22.99% and its median driver GTT peak grows 5.94%.
The movie is still about 6 decoded images/s. Full guest-state equality was
also not established. The runtime source and executable were restored.

## What was not verified

A standalone test on the actual RX 560X exercised cached and faithful memory
selection, incompatible memory masks, coherent fallback, and repeated GPU
writes followed by CPU reads. All 8 MiB of checked output matched literal
expected values. This proves the mapped-memory transfer behavior, not full
PS1 guest-state equivalence.

`tests/agent/filters_matrix.py` ran once against the candidate, redirected to
`build-perf`. All three 4x captures completed on the RX 560X, at 1280x896.
The comparison sheet was visually inspected: nearest and smooth filtering
behaved distinctly, with readable dialogue and intact sprites. This is not a
byte-identical software-renderer comparison or a complete playthrough.

A 24 FPS movie target, subjective audio quality, battles, long-term driver
memory growth, Windows, and operation under an enforced 8 GB memory limit were
not verified. The machine reports approximately 14.53 GiB of physical RAM.
Present timestamps measure CPU submissions, not physical monitor refresh.
Decoded-image rate is separate from present rate.

## Noticed, not done

- Capture and compile the movie's executed overlay routines through the existing
  system. CPU cores can compile independent routines ahead of playback; changing
  guest execution or adding decoder threads needs separate correctness evidence.
- Investigate map pacing before reconsidering the cached readback candidate.
- Fix the buffer destination-usage and host-visibility requirements independently
  as correctness work, with full renderer validation.
- Trace long-session driver-memory growth. The short fixed-work trials do not
  explain the much larger driver footprint seen in the earlier live session.
- Investigate the copied generated BIOS fingerprint warning separately.

## Experiment ledger and local evidence

| ID | Candidate | Primary median change | State proof | Cost | Verdict |
| --- | --- | ---: | --- | --- | --- |
| RB-20261005 | CPU-cached Vulkan readback | -39.19% field interval | GPU-written readback patterns identical; full guest state unverified | usage field per cached buffer, allocator selector, first-use log, transfer barrier | REJECT: secondary pacing and memory exceed 5% regression |

All paths below are relative to this worktree. Large traces, binaries, copied
checkpoints, and trial saves remain local and are not committed.

- `analysis/performance/fps-fix/campaign.json`: all six accepted runs and the plan.
- `analysis/performance/fps-fix/comparison.json`: all raw metrics, minima, and medians.
- `analysis/performance/fps-fix/A1/` through `B3/`: present timestamps, memory
  samples, current-device session logs, and each result.
- `analysis/performance/fps-fix/field.perf.data`, `field-profile.txt`,
  `field-callgraph.txt`: the valid first-field profile.
- `analysis/performance/fps-fix/video-confirmed.perf.data`,
  `video-confirmed-profile.txt`, `video-confirmed-callgraph.txt`,
  `video-profile-window.json`: the confirmed movie profile and mode/counter checks.
- `analysis/performance/fps-fix/rejected-readback.patch`: the reverted source
  candidate and its standalone transfer test.
- `analysis/performance/fps-fix/readback_bench.py`: the campaign script of fewer than 200 lines,
  using existing live helpers. It requires the archived candidate patch.
- `analysis/performance/fps-fix/readback-test.log`, `filters.log`,
  `field-diagnostics.json`: transfer results, regression results, and live
  overlay status.
- `analysis/agent/graphics-20261005T165158Z/cmp_all.png`: the inspected filter sheet.
- `analysis/performance/fps-fix/manifest.json`: original executable SHA-256
  `987d94178637e3a7f55b8ab6e8aa8a018f8cd8fa9b73b6872d92b71a33404982`.
- `analysis/performance/fps-fix/readback-plan.json`: candidate SHA-256
  `7b5cea774881e870feb5858ca312fd3f91c16fc0d02b03c25b3e93597cca4188`.

Two exploratory movie traces were excluded from movie conclusions: the first
had overlapping Start input, and the second lacked bounded before/after mode
checks. The final confirmed trace restored slot 10 and immediately profiled
without input. No performance pair was discarded or repeated.

# Static overlays and display ring, 2026-10-06

## What changed

- `psxrecomp/runtime/src/debug_server.c`: the always-on display ring is now
  opt-in (`PSX_DISPLAY_RING=1`). On Vulkan each capture was a full 1 MiB
  VRAM readback per frame, which is the 46% field cost found on 2026-10-05.
- `psxrecomp/tools/compile_overlays.py`: the generated static dispatcher also
  exports `psx_overlay_static_has_entry(addr)`, a lookup with no CRC gate.
- `psxrecomp/runtime/src/dirty_ram_interp.c`: the interpreter hands control to
  a compiled static overlay (a) when a guest call returns to an address with a
  compiled resume point, and (b) at local overlay transfers, which already
  did this for DLL overlays only. Each hand-over goes through
  `psx_overlay_dispatch`, which CRC-checks the live bytes.
- `CMakeLists.txt`: links `generated/overlays/overlays_static.c` when present.
- `tools/capture_overlays.py`, `tools/seed_overlay_entries.py`, and
  `tests/agent/bench.py` (fixed work: movie slot 10, 240 frames; field slot 3,
  600 frames; map slot 5, 300 frames).

Rebuild recipe (generated output stays local and is not committed):

```sh
python3 tools/capture_overlays.py
python3 tools/seed_overlay_entries.py analysis/performance/overlay/overlay_captures.json \
    analysis/performance/overlay/seeded_captures.json
python3 psxrecomp/tools/compile_overlays.py --static --cps --jobs 6 \
    --captures analysis/performance/overlay/seeded_captures.json --game-toml game.toml \
    --recompiler psxrecomp/recompiler/build/psxrecomp-game \
    --runtime-include psxrecomp/runtime/include --out-dir generated/overlays --gcc /usr/bin/gcc
cmake --build build-perf -j6 --target psx-runtime
```

48 of 49 captured regions compile (`PSX_SHARD_RESULT ok=48 failed=0 skipped=1`).

## The numbers

Runs were A1 (earlier), B6 A2 B7 A3 B8. A is the original executable (SHA-256
`987d9417…`, kept as `build-perf/ValkyrieRecomp.base`). B is the new build. Both
used default environment settings. Every run logged the RX 560X.

| Metric (median) | A | B | Change |
| --- | ---: | ---: | ---: |
| Field guest fps | 36.21 | 60.01 | +65.7% |
| Field present median ms | 27.52 | 16.66 | -39.5% |
| Field present p95 ms | 28.24 | 16.82 | -40.4% |
| Map guest fps | 26.58 | 51.26 | +92.9% |
| Map present median ms | 39.71 | 10.83 | -72.7% |
| Map present p95 ms | 64.06 | 31.66 | -50.6% |
| Movie guest fps | 21.90 | 21.67 | -1.1% |
| Movie decoded images/s | 6.00 | 5.93 | -1.1% |
| Startup s | 5.6 | 5.6 | 0% |
| Process RSS peak KiB | 604032 | 540284 | -10.6% |

Isolated contributions measured along the way: display ring off alone took the
field to 60 fps and the map to about 32 fps. The interpreter hand-over took the
map from about 32 to 51 fps. Static overlays without the hand-over changed
nothing measurable.

## What was not verified

Paired screenshots of the movie, field, and map matched visually
(`analysis/performance/overlay/shots/cmp-*.png`). Full guest-state equality,
audio, a full movie, battles, long sessions, Disc 2, Windows, and OpenGL were
not tested. No regression script covers the interpreter. Overlay coverage is
limited to the six save-state scenes, and other areas still run interpreted.

## Noticed, not done

- Movie playback is limited by device catch-up: `psx_devices_service_to_now`
  is about 41% inclusive and `psx_check_interrupts` about 20%, spread across
  DMA, CD-ROM, MDEC, timers, and the SPU sample event every 768 cycles.
- The capture recorder ignores code restored from a save state. A capture
  path that records dirty code regions without CD DMA would remove the
  movie-priming workaround.
- Debug-tools hooks (`debug_server_cyc_observe`, `debug_server_trace_write_check`,
  `xprobe_event`, `fntrace_record`) take about 6% in the movie and map. Release
  builds without debug tools do not pay this.
- `build-perf` configure warns that generated OpenBIOS is stale against the
  emitter fingerprint.

# Movie playback work, 2026-10-06 (later)

## What changed

- `game.toml` `[[overlays]]`: declares the movie decoder entries 0x8006147C and
  0x800614AC (the PsyQ VLC routine) for the 0x80060000 and 0x80061000 capture
  windows. It is reached through a pointer, and CD streaming into the same
  pages wipes the capture's entry evidence, so the compiler could not find it.
- `psxrecomp/runtime/src/cdrom.c`: `cdrom_cycles_to_irq` no longer reports a
  CD interrupt that is already presented (latched) as due. That made the
  deadline scheduler run a full device catch-up on nearly every guest cycle
  charge until the game acknowledged the interrupt: about 1.1 million
  catch-ups per guest second during the movie.
- `tools/capture_overlays.py` dumps several times per scene (`DUMPS_AT`) and
  takes `SLOTS=slot:secs,...` from the environment.

## The numbers

Two runs each, same fixed work as before:

| Metric | Previous commit | Now |
| --- | ---: | ---: |
| Movie guest fps | 21.67 | 28.35 / 28.28 |
| Movie decoded images/s | 5.93 | 7.67 / 7.70 |
| Field guest fps | 60.01 | 60.02 / 60.01 |
| Map guest fps | 51.26 | 51.20 / 50.30 |

Paired screenshots still match. A tested MDEC word-batching path in the device
catch-up added about 3% and was removed again.

## Decision

The movie is about 15 fps content, so full speed is about 16 decoded images/s.
The emulated pipeline is now limited by per-word MDEC DMA visibility, which is
deliberate. Further squeezing is not worth it: movies will instead be decoded
natively from the disc image and played directly (FMV replacement), with the
PS1-side movie skipped.

# MDEC DMA in whole blocks, 2026-10-06

## What changed

`psxrecomp/runtime/src/dma.c`: MDEC DMA in SyncMode 1 now lands each block
(BCR block size; Valkyrie Profile uses 32 words, CHCR 0x01000200) at the cycle
its last word was due, instead of one word at a time. The cycle cost per word,
the transfer end time, and the completion IRQ are unchanged. The scheduler's
next-event distance for an MDEC channel is the next block, not the next word.
`PSX_MDEC_BLOCKS=0` restores per-word stepping.

Basis: psx-spx (DMA Channels) states the CPU stalls on any RAM or I/O read while
DMA runs and resumes only between SyncMode 1 blocks, so word order inside a
block is not observable. DuckStation transfers MDEC DMA per block.

## The numbers

Alternating runs W0 B0 W1 B1 (W = per-word, B = blocks), same binary:

| Metric | Per-word | Blocks |
| --- | ---: | ---: |
| Movie guest fps | 28.39 / 28.07 | 41.83 / 42.05 |
| Movie decoded images/s | 7.71 / 7.66 | 11.39 / 11.53 |
| Field guest fps | 60.01 / 60.12 | 60.03 / 60.06 |
| Map guest fps | 50.54 / 50.98 | 49.40 / 50.16 |

Full opening movie from slot 10 to the title screen: both modes decoded 1169
images. Wall time was 162.8 s per-word and 113.4 s with blocks. Screenshots at
decoded images 30, 150, 400, and 800 are pixel-identical. On the title screen
after the movie, only the animated cursor strip differs.

## What was not verified

Audio during the movie. Battle Great Magic clips and dungeon video clips, which
use the same path, were not measured because no checkpoint reaches them.
The movie still runs below 60 guest fps.
