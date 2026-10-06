#ifndef PSX_RA_HOST_H
#define PSX_RA_HOST_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* RetroAchievements session. Inert (every call a no-op, hardcore off) when the
 * runtime is built without rcheevos or the player has not enabled it. */
int  ra_available(void);
/* Log in with a stored token, then identify the disc and load its set. */
void ra_start(const char *username, const char *token, int hardcore, const char *disc_path);
/* Blocking password login for the launcher (up to ~20 s). On success writes
 * the token to be stored instead of the password and returns 1. */
int  ra_login_password(const char *username, const char *password,
                       char *token_out, size_t token_cap, char *msg, size_t msg_cap);
/* Tell the server which disc is now in the drive after a swap. */
void ra_change_disc(const char *disc_path);
void ra_on_vblank(void);
/* 1 while hardcore is on and a game is loaded: cheats, save-state loading,
 * rewind and fast-forward must stay off. */
int  ra_hardcore_active(void);
/* One-line state for logs and the debug server. */
void ra_status(char *out, size_t cap);
void ra_shutdown(void);

#ifdef __cplusplus
}
#endif

#endif
