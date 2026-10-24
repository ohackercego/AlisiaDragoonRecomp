/* Alisia Dragoon USA: reset vector $0200; level 6 VBlank vector $005CAC. */
#include "game_spec.h"
#include "genesis_runtime.h"
#include <stddef.h>
#include <stdint.h>
#ifdef GENESIS_Z80_RECOMP
#include "alisia_z80_step.h"
#endif
static void alisia_call_entry(void) { recomp_call_addr(0x000200u); }
static void alisia_call_vblank(void) { recomp_call_addr(0x005CACu); }
static void alisia_call_hblank(void) { /* Level-4 autovector is a deliberate infinite trap loop ($0005A2). */ }
const GameSpec g_game_spec = {
 .display_name = "Alisia Dragoon", .short_name = "ALISIA",
 .expected_rom_size = 0x100000u, .tier3_floor_default = 1,
 .logical_players = 2u,
 .call_entry_point = alisia_call_entry, .call_vblank = alisia_call_vblank,
 .call_hblank = alisia_call_hblank, .resume_main_loop_pc = 0u,
 .save_resume_pc = NULL, .dispatch_main_loop_pc = 0u, .call_periodic = NULL,
 .on_post_reset = NULL, .on_frame_pre = NULL, .on_frame_post = NULL, .on_hblank = NULL,
 .handle_arg = NULL, .arg_usage = NULL, .dispatch_override = NULL,
 .fill_frame_record = NULL, .frame_record_version = 0u, .commands = NULL, .command_count = 0,
#ifdef GENESIS_Z80_RECOMP
 /* Statically recompiled sound driver (SmsRecomp --flat-step, z80/alisia_z80_step.c):
  * the scheduler keeps authority over reset/BUSREQ/interrupts; unknown live code
  * falls back per instruction to the SuperZazu interpreter inside the adapter. */
 .z80_step = alisia_z80_step,
#else
 .z80_step = NULL,
#endif
};
