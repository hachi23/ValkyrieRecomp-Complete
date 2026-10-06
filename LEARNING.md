# Learning log

How Valkyrie Profile, the PlayStation and this recomp work — explained in
plain language, one lesson per phase. Newest lessons go at the bottom.

---

## Lesson 0 — What a recomp is (2026-10-05)

Valkyrie Profile on the disc is a program written for the PlayStation's CPU.
Your PC's CPU can't run it directly, because the two speak different
**machine languages** — like a game cartridge that only fits one console.

**psxrecomp** reads the game's machine code and translates every instruction
into **C**, a programming language your PC can turn into a normal Windows
program. That translation step is the **recompile**. It's made from your own
copy of the disc, which is why the project never includes the game itself.

The translated game still expects to be inside a PlayStation: it wants a
graphics chip, a sound chip, a CD drive, memory cards and controllers. Your
PC has none of those, so psxrecomp includes a **runtime** that imitates each
piece. When the game says "draw this triangle", the runtime catches the
request and hands it to your graphics card.

How the planned features fit in:

- **Vulkan renderer** — the part of the runtime that draws the game's
  triangles and sprites using your AMD graphics card. Vulkan is the modern
  way to talk to a GPU; OpenGL is the older way.
- **Upscaling** — telling the renderer to draw everything at a bigger size
  than the PS1's original ~320×240 picture, so it looks sharp on a modern
  screen.
- **Cheats** — writing chosen numbers into the game's memory every frame
  (e.g. keep the HP value at max).
- **In-game overlay** — the runtime drawing its own menu on top of the game.
- **Logging** — the runtime keeping a diary of what happened, so a crash can
  be traced back to its cause.

### Words learned

- **Machine code** — the raw instructions a CPU understands.
- **Recompile** — translating a program from one machine's code to another's.
- **Runtime** — the software that pretends to be the PS1's hardware.
- **Renderer** — the part that turns drawing commands into pictures.
- **GPU** — your graphics card.
- **Emulator vs recomp** — an emulator translates the game *while it runs*;
  a recomp translates it *once, ahead of time*, so it runs as a native PC
  program.


## Phase 0 progress: identifying the undub discs (2026-10-04)

Your undub discs contain Japanese voices and English text. Their files differ from the retail discs, so the project's original disc check rejected them.
That rejection is expected. The check compares the disc against a list of known fingerprints before accepting it.

A fingerprint is a value calculated from a file's contents. Changing the contents changes the fingerprint.
We recorded both undub discs' fingerprints and added them to the accepted list while keeping the retail entry.
The project still checks the discs instead of bypassing that check.

The boot executable is the program the PlayStation starts when it loads the disc.
Both undub discs contain identical boot programs, and their loading details match the project's configuration.
You supplied both retail discs, and we compared their boot programs with the undub programs.
All four programs are identical byte for byte.
That comparison matters because the existing map of game functions describes the retail program.
It supports using that map unchanged. Matching loading details alone would not have proved this.

A baseline is a recorded run we use to compare later changes.
Our baseline will use OpenGL, the graphics system the project currently selects.
We still need to verify boot, the title screen, a field, a battle, the world map, a movie, and memory-card saving and loading.
We will also check Japanese voice playback and Disc 2 loading because the undub changes the disc contents.
Repeatable saves will let us revisit the same scenes when we test Vulkan and cheats later.

We installed the Vulkan SDK, a set of development tools needed to build Vulkan support, and verified that its shader compiler runs.
A shader is a small program the graphics card uses to draw the picture.
No game execution has been verified in this step. The Windows build with Vulkan support and the gameplay baseline remain pending.
The measured disc and executable facts are recorded in [the Phase 0 baseline record](docs/PHASE_0_BASELINE.md).

### Words learned

- **Fingerprint** is a value calculated from a file's contents to identify that file.
- **Boot executable** is the game program the PlayStation starts from the disc.
- **Baseline** is a recorded run used to compare later changes.
- **Save state** is a snapshot of the running console state, separate from the game's memory-card save.

## Phase 0 progress: translating the game and preparing the build (2026-10-04)

Both undub discs now pass the project's fingerprint check without skipping it. We also preserved the retail Disc 1 entry and added the supplied retail Disc 2 fingerprint.

The translation tools built successfully on Windows. They extracted the boot program from your verified Disc 1 and translated it into PC-compilable source files. Those files are generated output, so they stay local and are never edited by hand or committed.

The first game-build attempt stopped while downloading SDL, the library that supplies the game window, audio, and controller input. The portable CMake tool had no trusted certificate list configured. A certificate is how a download server proves its identity. We supplied a trusted certificate list and kept download verification enabled; SDL download then succeeded. This was a build-tool setup failure, not evidence of a game fault.

The game executable and actual gameplay still need verification.

### Words learned

- **Generated output** means files produced automatically by a tool from source inputs.
- **SDL** is a library that handles windows, sound, and controller input across operating systems.
- **Certificate** is part of how a secure connection checks the server's identity.

## Phase 0 progress: the first running build (2026-10-04)

The Windows game build succeeded with Vulkan included. We ran OpenGL first, as the plan requires, and saw the title screen and moving images from the opening movie. Including Vulkan in a build does not yet prove that Vulkan draws the game correctly. That is Phase 1 work.

A save state records the running console's memory and device state. We saved one during the opening movie, loaded it, and checked that both operations completed and the movie continued. This is separate from a memory-card save, which the original game writes itself. Memory-card saving and loading still need a real gameplay test.

A screenshot can show whether an image appears, but it cannot tell us whether the Japanese voices sound correct. Voice playback, controls during gameplay, the first field, first battle, world map, and the remaining checkpoint saves still need testing. Phase 0 is in progress.

### Words learned

- **Checkpoint** is a repeatable point in the game used to test later changes.
- **Memory-card save** is the saved progress the original game writes through its own save menu.

## Phase 0 progress: running on CachyOS and preparing analysis (2026-10-05)

The game now builds on your CachyOS laptop. We launched Disc 1 with OpenGL and the bundled OpenBIOS, the replacement for the console's startup firmware. The title screen appeared. We saved that scene in slot 1, restored it, and checked that both operations completed. This proves a repeatable title checkpoint on this laptop. It does not prove battles or memory-card saving yet.

The GameSir USB dongle is detected, and the game opens it as the Player 1 controller. Physical button response during gameplay still needs testing.

Ghidra is installed. Ghidra lets us inspect the original game's machine instructions and translate them into readable approximations. We imported the verified game executable at its correct memory address and requested a translation of its startup function. The result contains warnings, so we must compare the original instructions before drawing conclusions from it.

The bridge lets the coding agent ask Ghidra questions directly. It is configured to start when you log in. Poteto Mode and the pstack skills are installed as work instructions for the agent. Those instructions guide investigation and verification. They do not change the game or make unfinished gameplay checks pass.

The first field, first battle, world map, full movie with sound, Japanese voice playback, memory-card save and reload after restart, and Disc 2 gameplay remain unverified on this laptop. Phase 0 remains in progress.

### Words learned

- **Firmware** is the startup program supplied by the console.
- **Decompilation** produces an approximate readable version of machine instructions.
- **Bridge** connects the agent's tools to another program.

## Phase 0 progress: repeatable checkpoint testing (2026-10-05)

We added a small test runner that restores a recorded scene, sends a fixed controller sequence, and captures the result. The first recorded scene is the title screen. This gives us a repeatable starting point when we compare graphics or test later features.

The runtime first acknowledges a save-state request, then completes the request at a safe point. The runner waits for the completion report. Otherwise a test could continue before the game had actually restored the scene.

We replayed the title checkpoint twice and inspected the captured title screen. We also stopped a test while it held a button. The runner released its controller override, so the test does not leave the game stuck holding that button. An unavailable battle checkpoint fails clearly before contacting the game.

Scripted controller input reached the difficulty menu and selected Normal. This confirms the debug control path. The GameSir controller's physical buttons still need a separate check. A slot 2 state from the introduction was saved and restored successfully. The full introduction, voices, first field, battle, world map, and memory-card restart test remain pending.

A screenshot proves that the game produced an image. We must still inspect the image and separately check sound and game behavior. The test runner records those limits instead of treating every capture as a gameplay pass.

### Words learned

- **Input route** is a sequence of button presses measured in game frames.
- **Completion report** tells us whether a requested operation actually finished.
- **Controller override** supplies test input in place of the real controller until the test releases it.

Disc 2 also reached its title menu in a separate Linux run. We gave that run its own save directory so it could not overwrite the Disc 1 testing saves. Reaching the title proves that Disc 2 starts. We still need to load actual Disc 2 progress and test switching discs during play.

## Phase 0 progress: controlling the game with the keyboard (2026-10-05)

The keyboard now controls the running game through the normal input path. We checked that holding X presses the PlayStation Cross button and that releasing X releases it. This is different from the earlier debug-controller tests, which supplied buttons directly to the runtime.

Arrow keys moved Valkyrie around the Valhalla balcony. Walking left reached Frei, and keyboard input advanced the story into Odin's chamber and then the human world. The castle scene was waiting for us to move; the repeated background was not evidence of a broken game.

We saved the balcony scene in slot 3, restored it, and inspected it. The checkpoint runner also replayed that save successfully. A repeatable field scene lets us later compare the same character, background, and dialogue on different graphics settings.

The laptop's updated kernel files did not match the kernel still running in memory. The keyboard automation needed an input module from the running kernel. We loaded the matching module from the cached package without rebooting or downgrading the installed kernel.

We captured audio from the game's own sound output, without recording the microphone. The capture contains sound, but this session cannot listen to it. Japanese voice correctness and voice timing remain unverified.

### Words learned

- **Input path** is the route a real key press follows through the operating system and into the game.
- **Kernel module** adds a specific hardware or system capability to the running operating system.
- **Audio output** is the sound the game sends toward the speakers.

The story reached the world map, where the landscape is drawn in 3D instead of the side-view field layout. We saved that tutorial scene in slot 5, restored it, and inspected the captured terrain and characters. The game's own prompt showed START for spiritual concentration, so we used Enter. The later chapter map features still need gameplay testing.

## Phase 1 progress: Vulkan as the default, with a safety net (2026-10-05)

A **renderer** is the part of the recomp that turns the game's drawing commands into the picture on screen. This project has three. **Vulkan** is the modern way to talk to the graphics card. **OpenGL** is the older way. The **software renderer** draws everything on the main processor without the graphics card. It is slow but always works, and the project treats it as the reference for what a correct picture looks like.

The game now asks for Vulkan first. Before this change, if Vulkan could not start, the game dropped straight to the software renderer, skipping OpenGL. Vulkan can fail for ordinary reasons: a missing or broken graphics **driver** (the software that lets the operating system use the graphics card), or a card too old for Vulkan.

Now the game steps down one level at a time, like a game that lowers its graphics preset when your PC can't handle the higher one. It tries Vulkan, then OpenGL, then software. Before each step down, it cleans up everything the failed attempt left behind, then reopens the game window for the next renderer. The startup log now names the reason for every step down.

We tested this by starting the game while deliberately hiding the graphics driver from it. With Vulkan available, the game ran on Vulkan using this laptop's AMD Radeon chip. With the Vulkan driver hidden, it fell back to OpenGL. With the Vulkan driver hidden and OpenGL restricted to an old version, it fell back to software and kept booting. One rarer case, where the Vulkan window opens and the setup after it fails, could not be triggered on this laptop.

Gameplay on Vulkan is not tested yet. Every Phase 0 checkpoint still needs a Vulkan run at 1×, 2× and 4× internal resolution and at 4:3 and 16:9, compared with the software renderer.

### Words learned

- **Renderer** is the part that turns the game's drawing commands into pictures.
- **Driver** is the software that lets the operating system use a piece of hardware.
- **Fallback** is the backup choice used when the first choice fails.

## Phase 2 progress: the graphics settings menu (2026-10-05)

The launcher's Settings page now speaks plainly about graphics. Three options matter most.

**Internal resolution** is the size the game is drawn at before it reaches your screen. The PS1 drew pictures about 320 pixels wide and 240 tall. At 2× the recomp draws 640 × 480, and at 4× it draws 1280 × 960. The launcher now shows that size next to the choice, so "4x (1280 x 960)" tells you what you are getting. Valkyrie Profile is mostly hand-drawn 2D art. That art was painted at the PS1's size, so a higher internal resolution cannot add detail to it. It sharpens the 3D parts: the world map, battle effects, and small 3D objects like the floating crystal pointer over a speaker.

**Texture filtering** decides how the flat pictures painted onto shapes are stretched. "Nearest" keeps the hard square pixels. "Bilinear" blends neighbouring pixels, which looks softer.

**Display smoothing** decides how the finished picture is stretched to fill your window. Off keeps crisp edges. On blends them. This used to be called "Antialiasing" with choices of 2×, 4× and 8×, but the game only ever treated it as on or off, so the menu now shows exactly that.

All three work on Vulkan. Every option now says that it applies when the game starts or restarts.

We checked each one in the real game, using the Valhalla balcony save. A small test script starts the game once per setting, loads the save, and takes a full-size screenshot. The screenshots came out at 320, 640 and 1280 pixels wide for 1×, 2× and 4×. Bilinear filtering changed about 3 % of the picture (the parts with stretched textures). Display smoothing changed over half of the on-screen pixels. We also changed settings in the launcher, pressed Play, and confirmed the choices were saved and the game started with them.

While testing, we found that the debug screenshot tool always captured Vulkan at 1×, even when the game was drawing at 4×. It was copying from a small backup copy of the picture instead of the real one in the graphics card's memory. We fixed the tool so it reads the real picture. Without that fix, every later Vulkan comparison would have been comparing the wrong images.

Not yet checked: battles, FMVs and the world map at each setting, 16:9, and changing these options while the game is running (that comes with the in-game menu in Phase 3).

### Words learned

- **Internal resolution** is the size the game is drawn at inside the recomp.
- **Texture** is a flat picture painted onto a 3D shape or sprite.
- **Filtering** is how a picture's pixels are blended when it is stretched.
- **Pixel** is one dot of colour on the screen.

## Phase 3 progress: the cheat engine (2026-10-05)

A **GameShark code** is an instruction to change one number in the console's memory. The PS1 has 2 MB of main **RAM** (the game's short-term memory). Every changing value in the game lives somewhere in it: HP, gold, item counts, which menu is open. A code like `8005A7BC 0000` means "at memory address 0005A7BC, write the value 0000". The `80` at the front says "write two bytes". A `30` writes one byte.

Some codes are **conditional**. `D005A7BC FFFF` means "only if the value at 0005A7BC is FFFF, do the next line". The original GameShark worked the same way. It was a cartridge that sat between the console and the game and rewrote memory about 60 times a second, once per frame.

Our engine does the same job inside the recomp. Once per **frame** (one full redraw of the screen, about 60 per second), at the moment the PS1 signals **VBlank** (the short pause after drawing a frame), the engine runs every cheat you have switched on. It writes through the same path the game's own instructions use. That matters because one of your cheats rewrites part of the game's program, not just a number, and the recomp must notice program changes to run them correctly.

Cheats only run when three things are true: Assist Tools is on, Safe mode is off, and online play is off. Turning a cheat off stops its writes. It cannot undo what already changed while it was on. If infinite items kept an item count at 99, that count stays 99 until the game changes it.

The cheat list lives in `cheats/SLUS-01156.toml`. Each entry has an id, a name, the codes, a note, where it came from, and whether we have tested it in play. The list says which disc it belongs to, and the game refuses to load a list made for a different disc, because the same memory address can mean something completely different in another game.

We tested this in the running game. On the Valhalla balcony save, we switched on the "infinite item use in battle" cheat, wrote its trigger value into memory ourselves, and read the value back three frames later. With Assist Tools off, the cheat did nothing. With Assist Tools on, it rewrote the value as its codes say. With the cheat switched off again, it did nothing. None of the five cheats has been tested in real play yet.

### Words learned

- **RAM** is the console's short-term memory, where every changing value in the game lives.
- **Memory address** is the numbered location of one value in RAM.
- **GameShark code** is an instruction to write a value at a memory address.
- **Conditional code** only runs the next line when a memory value matches.
- **Frame** is one complete redraw of the screen.
- **VBlank** is the short pause after each frame is drawn.

## Phase 3 progress: cheats in the launcher and in the game (2026-10-05)

**In the launcher.** The launcher now has an **Assist Tools** page. It lists every cheat from the cheat file with a tick box, a search box, a "Disable all" button, and an "Untested" label until we confirm a cheat in real play. The page existed in the launcher code before, but a small bug made its button do nothing. The launcher only allowed opening pages up to "Mods" in its list, and Assist Tools came after it. Fixing one comparison made the page reachable.

**Safe mode** is a tick box on that page. It starts one run with every cheat off, without forgetting which cheats you picked. If the game ever crashes with cheats on, Safe mode is the quick way to check whether a cheat caused it.

**In the game.** Press **F5** on the keyboard, or **Select + Triangle** on the controller, to open the **Cheats & Graphics** menu. The game freezes while it is open, like a pause menu. Move with the D-pad or arrow keys, press Cross or Enter to change the highlighted row, and press Circle or Escape to close. You can switch Assist Tools and each cheat on or off, turn every cheat off at once, switch texture filtering (it changes right away), and pick an internal resolution (it applies the next time the game starts, because the graphics card's drawing space is created at that size when the game opens). Every change shows a short message at the top of the screen and is saved immediately, so it survives a restart.

The menu is drawn by the recomp itself as a plain picture laid over the game, the same way the save-state menu is. That is why it looks a little retro, and why it works the same on Vulkan, OpenGL and the software renderer.

We tested the launcher by scripting clicks: ticking a cheat and pressing Play saved it, the game reported it as active, the launcher showed it ticked the next time, and Safe mode ran with cheats off while keeping the choice. We tested the in-game menu with real key presses: the game advanced only 14 frames in 5 seconds while the menu was open, Enter switched on Assist Tools and a cheat, the choices were saved to the settings file before the menu closed, and the game resumed afterwards.

Still to do in Phase 3: remembering which cheats were on inside each save state, with a warning if you load a save state made with different cheats. Still needs you: trying each cheat in real play, and the controller combo on your GameSir pad.

### Words learned

- **Assist Tools** is the master switch for cheats and other player helpers.
- **Safe mode** starts one run with every cheat off.
- **Overlay** is a picture the recomp draws on top of the game.
- **Toast** is a short message that appears briefly on screen.

## Phase 3 finished: save states remember cheats (2026-10-05)

A **save state** is a snapshot of the whole console at one moment. If you made it with infinite items on and load it later with that cheat off, the game is in a state no normal play could reach. That can confuse you, or look like a bug. Each save state now gets a tiny companion file listing the cheats that were on. When you load it with different cheats, the game says "Save state used different cheats (1 then, 0 now)". Your older save states have no companion file and load quietly as before.

## Phase 4: logs and crash reports (2026-10-05)

A **log** is the game's diary. Each time you play, the recomp writes `logs/session-<date>-<time>.log` next to the game. Each line has the time and the **guest frame number** (how many frames the game has drawn), followed by what happened: which graphics card and driver were used, your graphics settings, which disc, which cheat list, cheats switched on or off, save states saved or loaded, and any time the game had to step down from Vulkan. Every line is written to disk straight away, so even a crash cannot lose the end of it. The last 10 logs are kept.

A **crash report** is a detailed snapshot taken at the moment the game crashes: what the PS1 processor was doing and what the recomp was doing. The project already wrote one, but each run replaced the last one. Now each real crash is also copied to `logs/crashes/` (the last 20 are kept), and each report also lists the cheats that were on, cheats switched in the last 10 seconds, the last save state you loaded, and which session log goes with it.

While the game runs, a small **marker file** (`logs/running.txt`) says "a session is running". A normal exit deletes it. If the game crashes, or the PC loses power, the marker stays. The next time you start, the launcher sees it and opens on the Assist Tools page with "Previous run ended unexpectedly", the cheats that were on, and the Safe mode box ready to tick.

If you suspect a cheat broke something: tick Safe mode and play the same part. If it works, switch half your cheats back on and try again, then halve again. This is called **bisecting**: halving the suspects each round finds the culprit quickly.

We tested this with a deliberate crash, a debug command that crashes the game on purpose. The crash report named the cheat that was on and when it was switched on. The launcher showed the notice on the next start, Safe mode kept cheats off, and a normal exit removed the marker.

### Words learned

- **Log** is a running diary of what the program did.
- **Guest frame number** is how many frames the game itself has drawn.
- **Crash report** is a snapshot of the program's state when it crashed.
- **Marker file** is a small file whose presence alone signals something, here "a run is in progress".
- **Bisecting** is finding a culprit by halving the suspects each round.

## Phase 3 extra: adding your own cheats (2026-10-05)

The Assist Tools page in the launcher can now edit the cheat list. There is only one list, `cheats/SLUS-01156.toml`, and the game reads nothing else.

**Pasting.** Copy codes from a website and paste them into the box. You can paste one cheat or a whole page of them: any line without codes is treated as the name of the codes below it. While you type, a line under the box says what will happen, for example "Ready to add 1 cheat. 1 cheat already in your list. Will skip "Bad One" line 1: Unsupported GameShark opcode". A code is checked by the same engine that runs it in the game, so a code the box accepts is one the game can run. Accepting a code does not prove it does what its name says. That still needs testing in play.

**Importing.** "Import file" reads the cheat files people share online: RetroArch `.cht` files, the `[Name]` style used by DuckStation, PCSX and ePSXe, and plain text files. Cheats already in your list are skipped, so importing the same file twice does nothing.

**Replacing.** "Replace all with file" swaps your whole list for the file's cheats. It asks for a second click, and it saves the old list as `SLUS-01156.toml.bak` first, so a wrong file cannot lose your cheats.

**Deleting.** Every cheat has a Delete button. Click it twice to remove the cheat.

A **duplicate** here means a cheat with exactly the same codes as one already in the list, even under a different name.

### Words learned

- **Import** is reading someone else's file into your own list.
- **Duplicate** is a cheat whose codes are already in the list.
- **Backup** is a copy kept before a risky change, so it can be undone.

## Phase 5: release builds (2026-10-05)

A **release** is a package other people (or you on another PC) can install without the project's source code setup. Because the game itself belongs to Square Enix, a release can never contain it. Our release zip contains the recomp's runner, its translation tools, the project settings and the cheat list. On first start, a **setup wizard** asks for your disc, translates the game into C, and **compiles** it (turns the C into a program your PC runs). This is called a **setup-host** release.

**Building releases.** GitHub can build releases for you (this is called **CI**, continuous integration: computers that build and test on their own). A private repository gets 2,000 free CI minutes a month, and Windows minutes count double. Mac minutes count ten times, and nobody here plays on a Mac, so the Mac builds are switched off. CI only runs when you create a version tag or start it by hand. Day to day, `scripts/local_release.sh` builds the same Linux zip on this laptop for free, in a separate temporary copy, so your saves and working files are never touched.

**What we tested.** We built the zip, unpacked it into an empty folder, ran the same translate-and-compile steps the wizard runs, using your Disc 1, and started the result. It reached the title screen on Vulkan with your cheat list loaded. We also checked that the zip contains no disc, no Sony BIOS, no saves and no translated game code. The only BIOS inside is OpenBIOS, a free replacement that may be shared.

**A bug this found.** The fresh install showed the title screen squeezed to one side. Two problems were hiding together. First, the Phase 1 safety-net change made the game make the window full-size after Vulkan had already measured it. Second, on this Linux desktop the graphics driver never tells Vulkan when the window changes size, so Vulkan kept drawing at the old size and the desktop stretched the picture. Vulkan now checks the window size every frame and rebuilds its drawing surface (the **swapchain**, the set of pictures it takes turns drawing into and showing) when the size changes. That also fixes resizing the window by hand.

Not yet tested: the Windows release (it builds on GitHub's Windows computers, which need a tagged release to run), and clicking through the setup wizard itself, including its download of build tools.

### Words learned

- **Release** is a packaged version for installing and playing.
- **Compile** is turning source code into a program the PC can run.
- **CI** (continuous integration) is computers that build and test automatically.
- **Swapchain** is the set of pictures Vulkan draws into and shows in turn.

## Phase 6 progress: extras, and two new picture filters (2026-10-05)

**Extras that already existed.** Several "quick wins" were already in the project, just not where the plan expected. Fast loading and a faster virtual CD drive are on the launcher's **Mods** page (both off). So is **PGXP**, which steadies the slight wobble of PS1 3D shapes. High-quality sound and CRT-style **Screen model** are on the Settings page.

**Skip movies did not work for this game.** The project's generic movie skipper watches the PS1's movie-decoding chip and presses START for you while it is busy. Valkyrie Profile's opening movie never touches that chip, so the skipper never noticed it, even though pressing START yourself does end it. Making this work needs a Valkyrie Profile–specific signal for "a movie is playing", found by studying the game's code. That is Phase 7 work, so the feature was left out instead of shipping a switch that does nothing.

**Smooth texture filter.** A **texture** is a small picture painted onto a shape or used as a sprite. "Smooth" looks at each corner of each texture pixel and asks whether a diagonal edge passes through it. If so, it draws the corner as a clean slope instead of a stair-step. This is the idea behind the **xBR** family of pixel-art filters. On Valkyrie's sprite, hair and face outlines become clean diagonals. It deliberately ignores weak edges, because the first version treated the background's dithering as edges and covered it in a crosshatch. Thin text can pick up small slanted cuts, because the dialogue font is drawn the same way as sprites.

**De-dither.** **Dithering** is mixing two colours in a checkerboard to fake a third. The PS1 art uses it in skies, walls and gradients. De-dither finds small two-colour checkerboards in a texture and blends them into the colour they were imitating.

Both are off by default, work on Vulkan, and can be changed from the launcher or in-game with F5. On OpenGL, Smooth acts like bilinear and De-dither does nothing.

### Words learned

- **Texture** is a small picture painted onto a shape or used as a sprite.
- **xBR** is a family of filters that redraws pixel-art edges as smooth slopes.
- **Dithering** is mixing two colours in a pattern to fake a third.
- **PGXP** is a fix for the PS1's slightly wobbly 3D positions.

## 2026-10-05: Why the GPU can be idle while a movie is slow

The renderer, the part that turns drawing commands into pictures, is using
Vulkan on the RX 560X. The movie still needs the CPU to run the PS1 game code
and keep its devices in time. When that work is slow, the GPU waits for the
next picture. A lightly used GPU does not automatically mean software rendering.

Some game code is loaded from the disc during play. These pieces are called
overlays. This configuration does not enable the compiled overlay cache, so
newly loaded code has to be interpreted one instruction at a time. The movie
profile showed instruction execution and device timing taking much more work
than image decoding. Adding decoder threads would therefore miss the largest
measured costs. The PS1's instruction order must stay intact even on a laptop
with many CPU cores.

The field scene had a separate problem. Its debug recorder repeatedly copied
video memory back to the CPU through memory without CPU caching. A tested
cached-memory allocation brought that scene from about 36 to 60 FPS. The movie
stayed around 6 decoded images per second. World-map median frame time and
GPU-driver system-memory use worsened beyond the agreed limits, so the change
was reverted. A fast result in one scene is not enough to keep an optimization.
The original executable and settings are restored. The report and raw results
remain available for the next investigation.

Words learned:

- Overlay: game code loaded during play instead of staying in the original executable.
- Interpreter: a program that runs each console instruction individually.
- Readback: copying GPU-produced data into memory the CPU can read.
- CPU cache: fast storage that helps the CPU repeatedly access memory.
- Frame pacing: how evenly pictures arrive, separate from their average rate.

## 2026-10-06: Native code for overlays, and switching off a costly recorder

Two changes made the field and the world map much faster. The movie did not change.

**1. A debug recorder was slowing every scene.** The developer build keeps a
"display ring", a rolling recording of the last few screens for debugging. On
Vulkan, recording one screen means asking the graphics card to copy all of its
video memory (1 MiB) back to the CPU, every frame. It is like pausing a game
every frame to take a screenshot. That recorder is now off unless someone turns
it on (`PSX_DISPLAY_RING=1`). The game never uses it.

**2. Overlays now run as native code.** Overlays are pieces of game code loaded
from the disc while you play. The recompiler turned the main program into PC
code ahead of time, but it never saw the overlays, so they ran on the
interpreter, which reads and acts on one PS1 instruction at a time. That is
much slower, like reading a recipe one word at a time instead of knowing it by
heart. The framework already had a way to record overlays while playing and
turn them into PC code. Three problems kept it from working here:

- It needs to know where each function starts. The recording held almost no
  start points, so 11 of 15 code areas were skipped. A small new tool,
  `tools/seed_overlay_entries.py`, finds them: places the code calls into, and
  places right after another function returns that set up their own workspace.
- The recorder only notices code that arrives from the CD. Loading a save state
  does not count, so each scene is recorded in a fresh game after playing a few
  seconds of the movie (`tools/capture_overlays.py`).
- The game's main loop runs forever. After a save state or an interrupt it was
  resumed inside the interpreter and never left, because the interpreter only
  checked for PC code when entering a function from its start. It now also
  checks when a call returns and when overlay code jumps. Every hand-over still
  checks that the code in memory matches the bytes that were compiled.

Results, median of three alternating runs each on the RX 560X:

| Scene | Before | After |
| --- | ---: | ---: |
| First field | 36 fps | 60 fps |
| World map | 27 fps | 51 fps |
| Opening movie | 6.0 pictures/s | 5.9 pictures/s |
| Memory peak | 590 MB | 528 MB |

Screenshots of all three scenes match the old build.

The movie is still slow because most of its time now goes to keeping the
emulated hardware in step: the CD drive, memory transfers (DMA), the video
decoder chip (MDEC) and sound timing. Those parts are updated many thousands of
times per second. Making that cheaper is the next job, and it means changing
the emulator core carefully.

Still to check in real play: a full movie with sound, a battle, and a long
session. These were not tested.

Words learned:

- Display ring: a debug recording of recent frames. Off by default now.
- Native code: code the PC runs directly, instead of the interpreter.
- Function entry: the address where a piece of code starts.
- Interrupt: the hardware tapping the CPU on the shoulder (for example, "a new
  frame started"). The CPU stops, handles it, then resumes where it was.
- DMA: a helper that copies data between parts of the console without the CPU.

## 2026-10-06: Why movies stayed slow, and the decision to play them natively

A PS1 movie is about 15 pictures per second, not 60. The "60" in my reports is
the console's own heartbeat: an NTSC PS1 ticks 60 times a second (one VBlank
per TV refresh), and everything, including the movie, the CD drive and the
music, counts those ticks. If the emulated console only manages 28 ticks a
second, the whole console runs at about half speed, so the movie plays in
slow motion.

Two fixes took the console from 22 to 28 ticks per second during the movie:

- The game's own movie decoder (the routine that unpacks the compressed
  pictures) now runs as PC code. The compiler could not find where it starts,
  because the game calls it through a pointer and video data streaming into
  the same memory pages kept wiping the clues. It is now named in `game.toml`.
- A CD-ROM bug: after the drive raised an interrupt (its "data is ready"
  signal), the emulator kept saying the interrupt was due right now until the
  game answered. So it re-checked every piece of hardware after almost every
  instruction. Now it waits quietly.

The rest of the cost is recreating the PS1's video pipeline exactly, piece by
piece, in real time. Rather than squeeze that further, the movies will be
decoded directly by the PC from your disc and played like a normal video,
while the game skips its own copy. That is called FMV replacement.

Words learned:

- VBlank: the 60-times-a-second tick of an NTSC PS1, one per TV refresh.
- MDEC: the PS1's video decoder chip.
- FMV: full-motion video, the pre-rendered movies.
- FMV replacement: playing the movie on the PC directly instead of emulating it.

## 2026-10-06: Copying movie pictures in blocks

The PS1 moves decoded movie pictures from the video decoder chip (MDEC) into
memory with DMA, a helper that copies data without the CPU. Valkyrie Profile
asks for this in blocks of 32 words. While a block is being copied, the real
PS1's CPU cannot read memory at all; it only gets a turn between blocks.

The simulated hardware treated every single word as its own event and checked
every other device after each one, a million times per second of game time.
Since the game cannot see inside a block anyway, each block now lands in one
step, at the exact moment its last word would have arrived. The time charged
is the same. DuckStation, a well-known PS1 emulator, works the same way.

The opening movie now runs at 42 of the console's 60 ticks per second instead
of 28, and plays through in 113 seconds instead of 163. Pictures at the same
point in the movie are identical to before.

About 30 video clips on each disc use this path, not only the opening. Most
look like battle spell effects and animated dungeon backgrounds, so this
should help in those places too. That still needs checking in real play.

Words learned:

- DMA block: a fixed-size chunk a DMA copy moves before the CPU gets a turn.

## 2026-10-06: Phase 7 begins — the Skip Movies mod

**What a mod is here.** The launcher's Mods page lists optional features. Each
one is a small folder with a description file (the manifest) that says which
game it is for and what it switches on. Some mods also come with a "plugin",
a few lines of code built into the game that run when you tick the mod.

**How skipping works.** The game itself already lets you press START to end a
movie. The runtime's skipper just holds START for you while a movie plays.
The hard part is knowing *when* a movie is playing:

- Most PS1 games stream movie sound from the CD (XA audio) alongside the
  picture, and the skipper normally waits for both. Valkyrie Profile's movies
  have no XA sound, so the game setting `fmv_skip_no_xa` tells it the video
  decoder (MDEC) alone is enough.
- But Valkyrie Profile also uses the video decoder *during play*: battle spell
  effects and animated dungeon backgrounds. Holding START there would open
  menus mid-battle. Full-screen movies switch the TV picture into 24-bit
  colour; normal gameplay uses 15-bit colour. A new setting,
  `fmv_skip_require_depth24`, makes the skipper act only in 24-bit mode.

**Tested.** On the anime movie checkpoint, with the mod on, the movie ended in
about 2 seconds and the game faded to the title menu; with it off, the movie
kept playing. The title menu's "Opening Movie" turned out to be a story scene
drawn live by the game, not a video, so the skipper rightly leaves it alone.

**Still for you to check.** Tick "Skip Movies" on the Mods page, then confirm
the anime opening and (on Disc 2) the ending skip, and that big spells in
battle are not cut short.

Words learned:

- Mod: an optional add-on listed on the launcher's Mods page.
- Manifest: the description file that tells the launcher what a mod is and does.
- Plugin: a few lines of code inside the game that a mod switches on.
- 24-bit / 15-bit colour: how many shades the PS1 picture can show. Movies use
  the richer 24-bit mode; gameplay uses 15-bit.

## 2026-10-06: Text speed, fast-forward, and a slow cutscene fixed

**Text speed.** Valkyrie Profile's story scenes wait for each line's voice
clip, so instant text would not make cutscenes shorter. A Chinese fan patch
that skips lines warns that it puts voices out of sync. Instant text would
only help unvoiced text, and the text is compressed on the disc, so finding
it is real reverse-engineering work. You chose the built-in fast-forward
instead: hold Tab (or Select+L1 on a pad), or press F9 to toggle it. It speeds
up the whole console, so voices and scenes stay together.

**What testing showed.** Fast-forward works, but on this laptop it only
reaches about 1.1 to 1.3 times normal speed, because the console simulation
already uses most of the CPU at normal speed. It is turned off in
RetroAchievements hardcore mode.

**The slow cutscene.** The prologue (the wedding scene with falling petals)
ran at about half speed. The graphics driver was doing most of the work: the
renderer started and finished a separate "drawing pass" on the graphics card
for every see-through petal, about 700 times a frame, and the card had to
pause between each. Now consecutive petals share one drawing pass, each still
drawn in the same order. The scene runs at 56 to 60 frames per second instead
of 32, and the picture is identical.

Words learned:

- Fast-forward: running the whole console faster than real time.
- Graphics driver: the program that passes the game's drawing work to the
  graphics card.
- Drawing pass (render pass): one batch of drawing work handed to the card.
- Semi-transparent sprite: a see-through picture, like a petal or glow.

## 2026-10-06: The game on the Windows play PC

**What was done.** The project was cloned fresh onto the Windows 11 PC
(Ryzen 7 7800X3D, Radeon RX 9070 XT) and built there for the first time. The
game's code was regenerated from your undub disc, because generated code is
never stored in Git. Both discs passed the fingerprint check.

**Two small snags.** The game first refused to start with no message. Windows
was missing two helper libraries (DLLs: shared code files a program loads when
it starts) that the RetroAchievements connection needs for internet access.
They come with the compiler toolkit (MSYS2) and are now copied next to the
game. The free BIOS stand-in (OpenBIOS) was also rebuilt so it matches the
current recompiler.

**What testing showed.** On Vulkan the title screen, the opening anime, the
New Game difficulty menu, the Valhalla intro, the balcony (first field), Odin's
throne room and the Midgard world map tutorial all draw correctly at a steady
60 frames per second. Walking, dialogue boxes and portraits work. Save states
save and load, and a state made on Vulkan also loads on OpenGL, which draws
the same picture at 60 fps. Fast-forward reaches about 250 frames per second
(about 4x) here, versus 1.1 to 1.3x on the laptop: the faster processor
finally has room to spare.

**Good to know.** In this version Cross confirms and Circle cancels. Leaving
the title screen alone starts a demo (the "A tri-Ace Creation" scene and the
anime), so a button press can land in the demo instead of the menu.

**Not tested yet:** a battle, Disc 2, a memory-card save and load after a
restart, the Skip Movies mod on the Mods page, and real controller feel.

**Seal tracker dropped.** The Seal value (it starts at 80 and must be 37 or
less in Chapter 7 for the A ending) is already shown at the bottom of
Valkyrie's status screen, so an extra overlay is not needed.

Words learned:

- DLL: a shared code file a Windows program loads when it starts.
- Save state: a snapshot of the whole console at one moment; unlike a memory
  card save, it can be made anywhere.
- Attract demo: the scenes a game plays by itself when the title is left idle.

## 2026-10-06: Why widescreen became "Stretch to fill"

**The idea.** Real widescreen means the game shows more of the world to the
left and right, not a stretched picture. For 3D scenes the recomp can do that
automatically: it tweaks the maths that turns 3D positions into screen
positions (the GTE, the PS1's 3D maths chip) so more fits on screen.

**Why it does not suit Valkyrie Profile.** Its towns and dungeons are not 3D.
They are flat painted layers slid sideways like theatre scenery, so the 3D
trick has nothing to work on. A second mode makes the picture itself wider,
but the game only paints scenery where it thinks the screen is. On the
balcony test the right side filled in, a strip on the left stayed empty, and
at the end of a room there is simply no artwork beyond the edge.

**Hard-coded numbers.** The game has the screen width, 320 pixels, written
straight into its instructions about 40 times instead of reading it from one
place. Raising all of them to 400 in a live test barely changed anything, so
the missing left strip is decided somewhere else. Finding it, and doing the
same for battles and dungeons, would be a long reverse-engineering job.

**What we did instead.** Like the DuckStation emulator, the Aspect ratio
setting now offers "4:3 (Original)" and "Stretch to fill". Stretch takes the
finished 4:3 picture and scales it to cover the whole window or screen. The
game itself draws exactly what it always did, so nothing can break; things
just look a little wider than intended.

Words learned:

- Aspect ratio: the shape of the picture, width compared to height (4:3 is
  the old TV shape, 16:9 is a modern widescreen).
- Pillarbox: black bars at the sides when a narrow picture is shown on a wide
  screen.
- Hard-coded: a value written directly into the program's instructions
  rather than kept in one setting that could be changed.
- Culling: skipping things the game thinks are off screen so it does not
  waste time drawing them.

## 2026-10-06: Changing discs during play, and the Quick Menu

**Changing discs.** Valkyrie Profile comes on two discs and asks for Disc 2
near the end of Disc 1. On a real PlayStation you open the lid, swap discs
and close it. The port now does the same thing in software. It opens the
other disc image first, so a missing file cannot leave the drive empty. Then
it tells the console "lid open", waits two seconds and says "lid closed".
In the test the game itself showed its little "OPEN" lid icon, the icon went
away when the lid "closed", and the game kept running. Save states follow
the disc that is in the drive, so a state made on Disc 2 is filed as a
Disc 2 state.

**The Quick Menu.** F5 (or Select+Triangle on a pad) opens one menu with
sections: save states (pick a slot, save, load), game (change disc, fast
forward), cheats, and graphics (texture filtering, de-dither, internal
resolution, stretch to fill). Graphics changes are saved for next time.
Each row was tested by sending key presses to the game window only and
capturing that window.

**Two small things found while testing.**

- If you started a run on Disc 2 directly, its save states were filed
  under Disc 1. They are now filed under the disc that is actually in the
  drive.
- With the Vulkan renderer the menu is drawn at a fixed size, so on a big
  window or a 4K screen it looks small. OpenGL already scales it to fit
  the window. This is older framework behaviour, noted for a later fix.

Words learned:

- Disc image: a file (here a .cue plus a .bin) holding an exact copy of a
  disc.
- Lid open/close signal: the drive's report to the console that the lid
  moved, which is how the game knows to check which disc is inside.

## 2026-10-06: Settings grouped under headings

The launcher's Display card was one long column of about fifteen settings.
It now has four small headings: WINDOW (size, fullscreen, shape of the
picture, VSync), RENDERING (which graphics engine, resolution, smoothing),
TEXTURES (how the game's pictures are filtered) and PLAYBACK (rewind and
similar). A heading only appears when the game has at least one setting
under it. Nothing about what each setting does has changed; they were only
moved. The change lives in recomp-ui, the shared launcher code, on its own
branch `feat/display-subheadings`, so other games using that launcher get
the same layout.

Words learned:

- VSync: making the picture wait for the screen's next refresh so the
  image never shows half of one frame and half of the next ("tearing").
- Branch: a separate line of changes in git, kept apart until it is ready
  to be merged.

## 2026-10-06: The Diorama launcher theme

You picked the "Diorama" mockup, inspired by HD-2D games such as Octopath
Traveler, and it is now the launcher's real look. `game.toml` has a new
`[launcher] theme = "diorama"` line; remove it and the launcher goes back
to the PlayStation blue.

What makes the look:

- Colours: dark wood cards on a near-black room, cream text, brass edges,
  and a gold PLAY button with dark lettering.
- Two serif fonts: Cardo for normal text and IM FELL English SC for
  headings and PLAY. Both are free fonts under the SIL Open Font License,
  so they can ship with the game; their licence notes are in
  `recomp-ui/assets/common/fonts/NOTICE.md`.
- Brass L-shaped brackets with a small rivet in every card corner, plus a
  thin inner frame line.
- Soft lamp glows behind the cards. A first try stacked see-through
  circles, which showed visible rings ("banding"); the final version paints
  each glow as one smooth gradient instead.

Words learned:

- Theme: a named set of colours, fonts and decorations the launcher can
  switch between without changing its layout.
- Banding: visible steps in what should be a smooth fade, caused by
  building the fade out of a few flat layers.
- Open Font License (OFL): a licence that lets anyone use and ship a font
  for free, as long as the font itself is not sold on its own.

## 2026-10-06: One repo, and a launcher that grows with your screen

**One repo.** The project used to live in three git repositories: the game,
the psxrecomp framework and the recomp-ui launcher, glued together as
"submodules". It now lives in one, `ValkyrieRecomp-Complete`, so a change that
touches all three is a single save point. The old repos still hold the full
history.

**Why the launcher looked small.** Windows lets a program say "I handle
screen scaling myself". The game says that, so its pictures stay sharp. But
the launcher never actually did the scaling, so on a 1440p screen set to 150
to 175% it drew everything at its original small size. Now it multiplies all
its sizes and fonts by your screen's scale. A new setting, Settings > SYSTEM >
Launcher text size, picks Auto or a fixed size from 100% to 200%. The launcher
never grows past the screen, so the whole app always fits.

Words learned:

- Display scaling (DPI): how much Windows enlarges text and windows so they
  stay readable on sharp, high-resolution screens.
- Monorepo: one repository that holds several projects that change together.

## 2026-10-06: Three fixes (achievements, menu size, resolution)

**Achievements could not log in.** The game talks to the RetroAchievements
website over HTTPS, the locked version of the web. Before trusting a website,
the program checks its ID card (certificate) against a list of trusted
issuers. Our copy of the web library (libcurl) shipped without that list, so
every check failed before the website even heard us (error 77). The fix tells
it to use the list Windows already keeps. Tested with your account: logged in
and found Valkyrie Profile, 0 of 174.

**The F5 menu was tiny.** The menu is drawn as a 640x480 picture, the size
of an old TV screen. The OpenGL and software paths stretched it to the
window. Vulkan pasted it pixel for pixel, so on a 1440p screen it covered a
third of the height. Now Vulkan enlarges it by a whole number (3x at 1440p,
2x at 1080p, 4x at 4K), so it fills the screen and stays crisp. Pop-up
messages and the volume bar got the same treatment.

**Internal resolution up to 16x.** The game draws into a copy of the PS1's
video memory, 1024x512 pixels, multiplied by the internal resolution. At 16x
that is 16384x8192, which is the largest picture most graphics cards accept,
so 16x is the ceiling. Vulkan now allows it; OpenGL and software stay at 4x.
If a card is smaller or runs out of memory, the game drops back to what fits
and notes it in the session log. Measured: 16x runs at 60 fps on the RX 9070 XT.

Words learned:

- HTTPS certificate: a website's signed ID card, checked against a trusted list.
- CA bundle: the trusted list of certificate issuers.
- Swapchain: the set of screen-sized pictures the graphics card takes turns showing.
- Nearest-neighbour scaling: enlarging by repeating each pixel, which keeps edges sharp.

## 2026-10-06: Phase 0, making breakage visible

The project has 47 small test programs that check the code. 8 of them had
been failing for weeks and nobody noticed, because nothing ran them. A
smoke alarm with a dead battery is worse than none, because you trust it.

What was wrong came in three kinds.

- **Windows quirks in the tests.** Two tests read or wrote text the Linux
  way. Windows reads files with a different alphabet table unless told
  "UTF-8", and writes a line break as two characters instead of one. The
  game was fine; the tests were not.
- **Stale tests.** Several tests check that an exact line of code exists.
  When someone improves the code, the line changes and the test fails even
  though nothing broke. For each one I looked up the change in the history
  and confirmed it was on purpose (for example, a fix that stopped another
  game from running old code). Then I updated the test to guard the new rule.
- **A real behaviour test.** One test actually builds and runs the overlay
  loader (the part that loads the game's swappable code chunks from disc).
  It needed stand-ins for ten newer connections and the new name of the
  cache folder. It passes every scenario now.

Two things worth knowing turned up and went into the plan (I1, I2). One
speed shortcut has fewer safety checks than its older version, and one old
shortcut is switched off but its code is still there.

New tool. `tools/dev/check.sh` builds the game, runs all 47 tests, checks
that the debug-command list is up to date, and opens the launcher to take a
screenshot. One command, then either "CHECK OK" or a list of what broke.

Words learned:

- Test: a small program that checks another program still behaves.
- Regression: something that used to work and broke again.
- Smoke test: a quick "does it even start" check.
- Stub: a stand-in piece that lets a test run part of a program on its own.

## 2026-10-06: Phase 1, quick seam fixes

A "seam" is a place where two parts of the program meet and only work
because someone kept them in step by hand. Phase 1 fixed seven small ones.

- **The game finds its files wherever you put it.** Settings used to store
  full addresses like `D:/.../disc/...`. Move the folder, or start the game
  from a shortcut, and it looked in the wrong place and made blank memory
  cards. Now a path inside the game folder is stored as "next to me"
  (`disc/Disc1/...`), like a save that remembers "third room on the left"
  instead of a street address.
- **Crash snapshots go into `logs/`.** When the game seems frozen it writes
  a snapshot of its memory (a "freeze dump") so we can see where it hung.
  Those used to land in whatever folder you started from.
- **A fresh build starts on its own.** The game needs helper files (DLLs,
  shared libraries other programs also use) next to it. The copy script
  stopped halfway, so a fresh build refused to start. It now copies all of
  them, and the build runs it.
- **Reinsert disc is a real hotkey.** Ctrl+C was a hidden debug key that
  opens and closes the virtual disc lid. It now has a Quick Menu row, a
  HOTKEYS row in the launcher, and you can rebind it. Useful if the game
  ever waits forever on the drive.
- **PlayStation button names.** The launcher showed Xbox-style names ("y",
  "r3"). It now says Triangle, Cross, R3, Left stick up.
- **Achievements follow disc changes.** RetroAchievements identifies a disc
  by its fingerprint (a "hash", a short code computed from the disc's
  data). When you swap to Disc 2, the game now tells the server, and the
  server confirmed it ("disc change accepted" in the log).
- **No reading past the end of a list.** The launcher copied 8 shortcut
  defaults from every game, even games that only have 2. Reading past the
  end of a list reads random memory. Valkyrie was safe; the Nintendo DS
  version was not. It now copies exactly as many as the game has.

Tested for real: Quick Menu > REINSERT DISC showed "Disc reinserted" and
the game kept running; the launcher's Controller and HOTKEYS pages show
PlayStation names and the Ctrl+C row; swapping discs with achievements on
logged "disc change accepted" both ways; all 47 tests pass.

Still for you to try: press Ctrl+C on the keyboard in game, and the
controller shortcuts on a real pad.

Words learned:

- Seam: where two parts of a program meet and must agree.
- Relative path: an address that starts from the game's own folder.
- DLL: a shared helper file a program loads when it starts.
- Hash: a short fingerprint computed from a file, used to recognise it.
- Out-of-bounds read: reading past the end of a list into unrelated memory.

## 2026-10-06: The watchdog that cried wolf

The game has a watchdog: a helper that runs beside the game and checks ten
times a second that it is still moving. If the game looks stuck for two
seconds, the watchdog writes a "freeze dump", a big snapshot of memory, so
we can see where it hung. Each one is 30 to 130 MB.

It was raising false alarms every time you played:

- **At the boot logo.** The watchdog also checks that the game's code is
  doing something new. During the PlayStation logo the BIOS (the console's
  built-in startup program) waits in one spot on purpose. That looked like
  a hang.
- **In the Quick Menu.** Opening a menu pauses the game, so its frames stop.
  To the watchdog, a paused game and a frozen game look the same.

Fixes. The menus now tap the watchdog on the shoulder while they are open
("I paused it on purpose"). If a menu itself hangs, the tapping stops and
the alarm still works. The logo check ignores the BIOS. And the game now
keeps only the 3 newest dumps in `logs/`, so the folder can never grow
without limit.

Tested: a 25 second boot and 8 seconds in the Quick Menu wrote nothing.
Then I froze the game on purpose (paused its main worker from outside) for
6 seconds, and the watchdog still caught it. The next start deleted the
extra old dumps.

Words learned:

- Watchdog: a helper that checks another program is still alive.
- False positive: an alarm that goes off when nothing is wrong.
- Thread: one worker inside a program; the game and the watchdog are
  separate workers, which is why the watchdog can see the game freeze.

## 2026-10-06: Phase 2, one source of truth

Before this phase, the game kept each setting in four different "shapes":
the live value the game uses, the line in `settings.toml`, the launcher's
copy, and a temporary copy in between. Eight separate blocks of code copied
values between them by hand. Adding one setting meant eight edits that had
to agree. Miss one, and that setting silently got lost on one path only.

Think of a party's stats kept in four notebooks, copied by hand every time
you rest at a save point. One slip, and a character's HP is wrong in one
notebook.

What changed:

- **Four copy rules instead of eight copy blocks.** There is now one rule
  for each direction: file to game, game to file, game to launcher,
  launcher to game. Both the normal start and the online "back to lobby"
  path use the same rules. The lobby path had drifted; it now also keeps
  de-dither and the borderless fullscreen choice.
- **One list of controller hotkeys.** The six controller shortcuts are one
  table instead of being spelled out in eight places.
- **One list of keyboard hotkeys per program, plus a referee.** The
  launcher's four lists of hotkey names, keys and defaults became one list.
  The game has its own one table. A test compares the two and fails if they
  ever disagree. The launcher now shows Fullscreen's real default too:
  Alt+Return or Ctrl+F.

How I proved nothing changed. A refactor ("refactor": reorganising code
without changing what it does) is only safe if you can show the behaviour
stayed the same. I built a test robot that writes a settings file full of
unusual values, opens the real launcher, presses PLAY, and saves the file
the game writes back. I recorded that with the old game first, then with
the new one. They are identical, byte for byte, for two different sets of
values. It also starts the game without the launcher and checks the
settings were applied. The robot now runs in `check.sh` every time.

What the robot found. With the old game too, the launcher quietly changes
a few things you set: a memory card you switched off comes back on, and
player 2's deadzone copies player 1's. That is finding K, a good next fix.

Words learned:

- Refactor: reorganising code without changing what it does.
- Source of truth: the one place a fact is stored; everything else reads it.
- Baseline: a recorded result from before a change, to compare against.
- Round trip: sending data out and back to check nothing got lost.

## 2026-10-06: Finding K, the launcher forgot two of your choices

The test robot from Phase 2 caught the launcher changing two settings
behind your back.

- **Memory card switched off came back on.** The launcher and the game pass
  each card as a number. 0 meant both "off" and "nobody set this yet", and
  the launcher turns "nobody set this" into "on". Like a save menu that
  shows an empty slot and a deleted slot the same way. Now "off" has its
  own number.
- **Player 2's deadzone copied player 1's.** The deadzone is how far you
  can push a stick before the game notices, so a worn stick doesn't drift.
  Long ago the launcher had one deadzone for everybody. Each controller now
  has its own, but an old rule still copied player 1's value onto player 2
  at every launch. I removed that rule and the leftover code behind it.

One change I left alone on purpose: a keyboard player's "Analog" setting
shows as "D-Pad". A keyboard has no sticks, and the game already treats it
as a D-pad. Plug in a controller and it goes back to Analog by itself.

Tested: the robot's settings file now comes back with your memory card
still off and player 2's deadzone kept, and the launcher shows card 2 as
off.

Words learned:

- Deadzone: the small stick movement the game ignores, to stop drift.
- Sentinel value: a special number that means "not set" instead of a real
  choice; trouble starts when it is also a real choice.

## 2026-10-06: Fullscreen, widescreen and a Linux version

**The fullscreen bug.** It was really a window-size bug. Your taskbar hides
itself, so the game made its picture the full height of the screen and
forgot the title bar on top. The window spilled off the top and bottom and
sat in the middle with the desktop showing at the sides: it looked like a
broken borderless fullscreen. The window now shrinks a little, keeping its
shape, until the whole thing fits. Real fullscreen (Alt+Enter) was fine all
along and still fills the screen.

**Widescreen.** Nobody has made a widescreen patch for the PS1 Valkyrie
Profile. Its towns, dungeons and battles are flat painted layers drawn only
for a 4:3 screen, so showing more would mean finding and changing the
drawing code for each kind of scene, and the edges of rooms have no artwork
to show. Stretch to fill stays the practical choice.

**Linux.** The same source code was compiled for Linux inside WSL (a Linux
system that runs inside Windows). The translated game code is the same on
both; only the outer program is rebuilt. `ValkyrieRecomp-Linux.tar` holds the
game, both discs and your saves. Unpack it on Linux with `tar -xf` and run
`./play.sh`.

Words learned:

- WSL: Windows Subsystem for Linux, a Linux system inside Windows.
- glibc: Linux's core system library; a program built on a newer Linux needs
  at least that glibc version.
- tarball: one file holding a whole folder, like a zip, that keeps Linux file
  permissions.
