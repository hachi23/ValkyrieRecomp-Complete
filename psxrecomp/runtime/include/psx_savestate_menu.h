#ifndef PSX_SAVESTATE_MENU_H
#define PSX_SAVESTATE_MENU_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void psx_savestate_menu_set_state(int open, int selected_slot);
void psx_savestate_menu_note_slots_changed(void);
int  psx_savestate_menu_needs_present(void);
int  psx_savestate_menu_overlay_image(const uint32_t **pixels, int *w, int *h);

/* A generic host list menu sharing the save-state menu's overlay slot.
 * Rows are "label  value"; the strings are copied. count 0 closes it. */
#define PSX_LIST_MENU_MAX_ROWS 64
void psx_list_menu_set(const char *title, const char *const *labels,
                       const char *const *values, int count, int selected,
                       const char *footer);

#ifdef __cplusplus
}
#endif

#endif /* PSX_SAVESTATE_MENU_H */
