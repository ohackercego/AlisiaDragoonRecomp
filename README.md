# Alisia Dragoon — Native Windows Recompilation

A **native x64 static recompilation** of *Alisia Dragoon* (USA, Sega Mega Drive /
Genesis, 1992, Game Arts) for Windows PC, built on the
[segagenesisrecomp](https://github.com/mstan/segagenesisrecomp) framework.

Both CPUs execute generated C instead of an interpreter:

| CPU | Status | Evidence |
| --- | --- | --- |
| Motorola 68000 (game logic, 1 MiB ROM) | **100% recompiled** | `[FLOORCOUNT] entries=0` at exit — zero ROM addresses fall back to the Tier-3 interpreter |
| Zilog Z80 (sound driver) | **statically recompiled** (8192 PC entries) | `[Z80RC] fallback_unique_pcs=8`, all in the reset window; audio output byte-identical to the interpreter |

**No ROM is included in this repository, and no recompiled output derived from it
is included either.** You must supply your own legally obtained ROM dump. The
build generates every source file from that ROM locally.

---

## Downloads

Prebuilt Windows x64 builds are on the [Releases](../../releases) page. Unzip,
put your ROM next to the executable, run it.

```
AlisiaDragoonRecomp.exe
SDL2.dll
settings.ini
alisia_usa.md        <- your own ROM (1 048 576 bytes)
```

Expected ROM identity:

```
size   1048576 bytes
sha256 cb4e9c98de5a048ccdddf03bcfa5d8aad678c2399f4c5651075009c59836ffd2
```

On first run the ROM picker appears once. After that the path is cached in
`rom-ALISIA.cfg` and `settings.ini` has `skip_launcher = 1`, so a double click
boots straight into the game.

---

## Controls

Defaults (rebindable in `settings.ini`, no launcher required):

| Mega Drive | Keyboard | Xbox-style pad |
| --- | --- | --- |
| D-Pad | Arrow keys | D-Pad / left stick |
| A | `Z` | `B` |
| B | `X` | `A` |
| C | `C` | `X` |
| Start | `Enter` | `Start` |
| X / Y / Z (6-button) | `A` / `S` / `D` | `Y` / `LB` / `RB` |
| Mode | `Backspace` | `Back` |

`settings.ini` carries `[input.p1]` … `[input.p4]` with

```
device    = 3      # 0 none, 1 keyboard, 2 gamepad, 3 both
pad_type  = 0      # 0 = 3-button, 1 = 6-button
deadzone  = 25
key.A = 29         # SDL scancode
pad.A = button:1   # SDL_GameController button index
```

Gamepads are hot-pluggable; the runner logs `[gamepad] P1: <name>` when one is
opened.

## Save states and rewind

| Key | Action |
| --- | --- |
| `Shift+F1` … `Shift+F9` | save to slot 1–9 |
| `F1` … `F9` | load slot 1–9 |
| `F7` / `F8` | rewind browser / save-slot menu |
| `Esc` | menu |

Files are `native_save_<slot>.bin` next to the executable (~157 KB each). A
savestate covers the 68K register file, 64 KB work RAM, VDP, bus, Z80 (including
the recompiled driver), YM2612 and SN76489 state. Rewind keeps 60 snapshots at a
6-frame interval.

Savestate correctness was verified two ways:

1. Save at frame 1221, load at 1521 → work RAM hash identical to the save point
   (`b1641a517e97`), zero differing bytes.
2. Two different histories reaching the same save (load immediately vs. 300
   frames later) → 61 frames after loading, work RAM identical
   (`c4fefa1d4497f4e5`). Nothing is left unrestored.

---

## What "native" means here — and what it does not

Three different things get called "emulation". Being precise:

1. **Guest code executed by an interpreter.** Eliminated. The 68K floor is empty
   and the Z80 runs generated C. Eight Z80 PCs still hit the interpreter, all
   inside the boot window where the 68K releases the Z80 reset before it has
   finished uploading RAM; they are transient and the audio output is
   bit-identical to the interpreter.
2. **Console hardware behaviour reimplemented in C.** This *is* native code, not
   an interpreter: the framework ships its own VDP, bus, DMA/scheduler, YM2612
   and SN76489 implementations, compiled into the executable. A sound chip has no
   instruction stream, so it cannot be "recompiled" — only emulated faithfully or
   rewritten by hand.
3. **Audio/video fidelity.** The YM2612 core is `ymfm`; the FM ladder effect and
   an optional parallel FM shadow are configurable in the framework.

### Real limitations of this build

- **Coverage is measured, not assumed.** 100% native was proven for the boot,
  the title screen, the menu and stage 1 (up to ~7 200 frames / 2 minutes). Later
  stages, bosses, the ending and the sound test have not been exercised yet, so a
  previously unseen 68K address could still appear. Every run prints
  `[COVERAGE] floor_entries=N z80_fallback_pcs=N` at exit (however you quit) and
  writes `floor_coverage.toml`; any address listed there is folded into
  `alisia_discovery.toml` and the build is repeated. That file is the to-do list
  for full-game coverage — see "Reporting coverage from a play session" below.
- **Video is the native VDP pass**, integer-scaled to the window. No per-game
  custom renderer, so no true widescreen and no pixel-perfect integer scaling at
  4K yet (a 320×224 source in a 3840×2160 window is a non-integer 12×9.64
  stretch).
- **Audio is the emulated YM2612/PSG**, not a native synthesiser. `--turbo`
  disables audio playback by design; do not use it when testing sound.
- **Windows x64 only.** No Linux/macOS builds in this repo.
- **No netplay, no cheats, no debugger UI** beyond the framework's diagnostics.

---

## Building from source

### Requirements

- Visual Studio 2022 (MSVC x64) + CMake ≥ 3.21
- [segagenesisrecomp](https://github.com/mstan/segagenesisrecomp) checked out at
  `d694c27` or newer
- [SmsRecomp](https://github.com/mstan/smsggrecomp) for the Z80 driver (only
  needed when regenerating `z80/alisia_z80_step.c`)
- Python 3 for the helper scripts

### Steps

```powershell
# 1. Framework + this repo side by side
git clone https://github.com/mstan/segagenesisrecomp.git ..\segagenesisrecomp
git checkout -C ..\segagenesisrecomp d694c27

# 2. Apply the game-side framework changes (cached-ROM boot, [FLOORCOUNT],
#    [Z80RC] coverage counters, audio stats)
git -C ..\segagenesisrecomp apply patches\segagenesisrecomp-alisia.patch

# 3. Put your ROM here (not in git)
copy <your-dump>.md .\alisia_usa.md

# 4. Rebuild the Z80 driver image from that ROM and regenerate its C
python tools\extract_z80_image.py alisia_usa.md
SmsRecomp.exe --game z80\z80game.toml --flat-step     # see z80\README.md

# 5. Configure and build
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 ^
      -DGENESIS_RECOMP_ROOT="%CD%\..\segagenesisrecomp"
cmake --build build --config Release --parallel
```

The 68K C sources are generated into `build/generated/alisia/` by `GenesisRecomp`
during the build — they are not stored in this repository, because they are
derived from the ROM.

Useful build switches:

- `-DALISIA_Z80_RECOMP=OFF` — run the sound driver through the SuperZazu
  interpreter instead (A/B reference for audio parity).

---

## Verifying the claims yourself

```powershell
# 68K floor + Z80 fallback coverage, printed at exit
.\AlisiaDragoonRecomp.exe --no-launcher --max-frames 950 .\alisia_usa.md
#   [Z80RC] fallback_steps=7951 fallback_unique_pcs=8
#   [FLOORCOUNT] entries=0

# Audio parity: same ROM, same frame count, two builds
.\AlisiaDragoonRecomp.exe --no-launcher --max-frames 3200 --wav on.wav --input-script start.input .\alisia_usa.md
# rebuild with -DALISIA_Z80_RECOMP=OFF, repeat -> SHA-256 of both WAVs must match
```

`start.input` example (frame-based input script understood by the runner):

```
WAIT 600
PRESS START 6
WAIT 220
PRESS START 6
WAIT 400
SAVE_STATE native_save_1.bin
```

Measurements from this repository's validation runs:

| Check | Result |
| --- | --- |
| 68K floor entries, boot | 0 |
| 68K floor entries, stage 1 (3 200 frames with START) | 0 |
| Z80 interpreter fallbacks | 8 PCs, boot window only |
| Audio WAV parity, 900 frames (boot) | identical, 0 differing bytes |
| Audio WAV parity, 3 200 frames (title → stage 1) | identical, `048fdd00acad9d2d` |

---

## Reporting coverage from a play session

The only way to prove full-game coverage is to play the whole game. Anyone can
contribute the evidence:

1. Play as far as you can (later stages, bosses, the ending). Quitting with `Esc`
   or closing the window both flush the logs.
2. Send back the files the runner wrote next to the executable:
   - `floor_coverage.toml` — 68K addresses that needed the interpreter
   - `dispatch_misses.toml`, `interior_label_misses.toml`, `floor_unsafe.toml`
   - the `[COVERAGE]` line printed at exit, if you ran it from a terminal
3. Each `floor_coverage` entry is verified as code, appended to
   `alisia_discovery.toml`, and the build is regenerated. When the list stays
   empty across a full playthrough, the 68K is 100% native for the whole game.

An empty `floor_coverage.toml` (`entries: 0`) is the success signal.

---

## Legal

- **No ROM and no ROM-derived source is distributed here.** You must own and dump
  your own cartridge.
- *Alisia Dragoon* is © Game Arts / Sega. This project is not affiliated with,
  endorsed by, or licensed by them. It exists for preservation and research on
  static recompilation.
- The framework (`segagenesisrecomp`) is distributed under its own licences; see
  its `LICENSE.md`, `LICENSE-recompiler` and the PolyForm Noncommercial terms used
  by the game mod interface. This repository only adds the game integration
  (spec, discovery list, build wiring, tooling).

## Credits

- [mstan/segagenesisrecomp](https://github.com/mstan/segagenesisrecomp) — 68K
  recompiler, runtime, VDP/bus/audio integration
- [mstan/smsggrecomp](https://github.com/mstan/smsggrecomp) — Z80 static
  recompiler used for the sound driver
- [SuperZazu/z80](https://github.com/Superzazu/z80) — Z80 interpreter used only as
  the per-instruction fallback
- ymfm — YM2612 core; SN76489 core from the framework
- Script/entity VM dispatch targets were identified from the framework's
  Tier-3 floor log and verified as code before being added to
  `alisia_discovery.toml`.
