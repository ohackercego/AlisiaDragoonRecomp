# Z80 sound driver — static recompilation

Alisia Dragoon's sound driver is not a separate Z80 program in the cartridge: the
68K boot code lifts it into Z80 RAM in two blobs, and the destination of the
second blob is computed from two bytes inside the first one.

```
68K:  block1  $08B784 + 0x1119 -> $A00000
      dst = ($A00018 << 8) | $A00017          (bytes inside block1)
      block2  $08C89E + 0x09FF -> $A00000 + dst      (here: $13A3)
```

Two ways to obtain the 8 KB image the driver actually runs:

1. **From the ROM (what this repo does).**
   `python tools/extract_z80_image.py alisia_usa.md` writes
   `z80/z80_driver_image.bin` and prints both destination ranges. Deterministic
   and reproducible from a clean dump.
2. **From a live run** (better fidelity: the driver rewrites ~950 bytes of itself
   at init). Dump the 8 KB Z80 RAM after the upload has completed, around frame
   900. Any capture method works; the file is exactly 8192 bytes.

Then:

```
SmsRecomp.exe --game z80/z80game.toml --flat-step --output-dir z80
```

which emits `alisia_z80_step.c` (~2.7 MB: one function per PC, 8192 entries) and
`alisia_z80_step.h`.

## How the runner uses it

- `CMakeLists.txt` defines `ALISIA_Z80_RECOMP` (default `ON`) and adds
  `runner/z80_recomp.c` from the framework plus the generated file.
- `alisia_spec.c` installs the entry point:

  ```c
  #ifdef GENESIS_Z80_RECOMP
  #include "alisia_z80_step.h"
  #endif
  ...
  .z80_step = alisia_z80_step,
  ```

- The scheduler keeps authority over reset, BUSREQ/acknowledge and interrupts;
  the adapter only replaces the instruction-stepping core. If the live bytes at
  a PC no longer match the captured image (self-modifying driver code), that one
  instruction falls back to the SuperZazu interpreter and the run continues.

## Coverage counters

At exit the runner prints:

```
[Z80RC] fallback_steps=<n> fallback_unique_pcs=<n>
```

Eight PCs is the expected value for a healthy boot: they are the partially
written RAM the Z80 executes between reset release and the end of the 68K upload.
A growing count across normal play means the driver patched new code that the
image does not contain — recapture the image (method 2) and regenerate.

## Audio parity check

With the same 68K build, `-DALISIA_Z80_RECOMP=ON` and `OFF` must produce
byte-identical WAV output for the same frame count:

```
AlisiaDragoonRecomp.exe --no-launcher --max-frames 3200 --wav on.wav \
    --input-script start.input alisia_usa.md
```

Measured: identical for 900 frames (boot) and 3 200 frames (title → stage 1).
Do not compare across builds with different 68K discovery lists — that changes
68K timing and therefore the audio stream.
