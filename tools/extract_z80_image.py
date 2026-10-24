#!/usr/bin/env python3
"""Reconstruct the Z80 sound-driver image from your own Alisia Dragoon ROM.

The 68K boot code uploads two blobs into Z80 RAM:

    move.l #$08B784,a0 / move.w #$1119,d0   -> $A00000      (0x1119 bytes)
    dst = ($A00018 << 8) | $A00017           -> $08C89E      (0x09FF bytes)

The second destination is computed from two bytes *inside* the first blob, so
the image has to be rebuilt in that order. Output: z80/z80_driver_image.bin
(8192 bytes), which is the input for the SmsRecomp --flat-step step.

Usage:  python tools/extract_z80_image.py <rom>  [-o z80/z80_driver_image.bin]
"""
import argparse
import pathlib
import sys

ROM_SIZE = 0x100000
BLOCK1_SRC, BLOCK1_LEN = 0x08B784, 0x1119
BLOCK2_SRC, BLOCK2_LEN = 0x08C89E, 0x09FF


def build_image(rom: bytes) -> bytes:
    if len(rom) != ROM_SIZE:
        sys.exit(f"expected a {ROM_SIZE}-byte ROM, got {len(rom)}")
    img = bytearray(0x2000)
    img[0:BLOCK1_LEN] = rom[BLOCK1_SRC:BLOCK1_SRC + BLOCK1_LEN]
    dst = (img[0x18] << 8) | img[0x17]
    if dst + BLOCK2_LEN > len(img):
        sys.exit(f"second blob would overflow Z80 RAM (dst=${dst:04X})")
    img[dst:dst + BLOCK2_LEN] = rom[BLOCK2_SRC:BLOCK2_SRC + BLOCK2_LEN]
    print(f"block1 $A00000..$A{BLOCK1_LEN - 1:04X} ({BLOCK1_LEN} bytes)")
    print(f"block2 $A{dst:04X}..$A{dst + BLOCK2_LEN - 1:04X} ({BLOCK2_LEN} bytes)")
    print(f"nonzero bytes: {sum(1 for b in img if b)}")
    return bytes(img)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("-o", "--out", default="z80/z80_driver_image.bin")
    args = ap.parse_args()

    data = pathlib.Path(args.rom).read_bytes()
    img = build_image(data)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img)
    print(f"wrote {out} ({len(img)} bytes)")


if __name__ == "__main__":
    main()
