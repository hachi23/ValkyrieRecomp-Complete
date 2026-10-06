/* Game-owned mod plugins for Valkyrie Profile. Each is activated by a feature
 * in mods/preloaded/packages when the player enables it on the Mods page. */
#include "mod_plugins.h"

/* valkyrie.skip-fmv: VP's movies stream MDEC video with no XA audio, so the
 * runtime detector needs [video] fmv_skip_no_xa plus fmv_skip_require_depth24
 * in game.toml (battle and dungeon clips decode into 15-bit scenes). */
static void vp_skip_fmv_activate(void) {
    (void)psx_mod_set_auto_skip_fmv(1);
}

PSX_MOD_CONSTRUCTOR(vp_register_mod_plugins) {
    (void)psx_mod_register_activation_plugin("valkyrie.skip-fmv",
                                             vp_skip_fmv_activate);
}
