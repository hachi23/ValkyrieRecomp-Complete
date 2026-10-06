#ifndef PSX_SESSION_LOG_H
#define PSX_SESSION_LOG_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Low-volume event log for one run (the ValkyrieRecomp fork's deliberate
 * exception to "no log files"): logs/session-YYYYMMDD-HHMMSS.log, last 10
 * kept, one flushed line per event stamped with wall time and guest frame.
 * A logs/running.txt marker exists while a run is live; finding it at the
 * next start means that run ended without a clean exit. */
void session_log_open(const char *logs_dir);
void session_log_event(const char *fmt, ...);
/* Latest active-cheat list; logged and kept in the marker for crash reports. */
void session_log_set_active_cheats(const char *csv);
void session_log_note_state_load(int slot);
/* Clean shutdown: removes the running marker. */
void session_log_close(void);

const char *session_log_path(void);
/* The logs folder given to session_log_open, or "" before it is opened. */
const char *session_log_dir(void);
/* Text from a previous run's leftover marker, or NULL. Valid until exit. */
const char *session_log_previous_crash(void);

/* JSON object body (no braces) for the crash report. Signal-context safe:
 * reads static buffers only. */
size_t session_log_crash_json(char *out, size_t cap);
/* Copy a crash report into logs/crashes/crash-<stamp>.json, keeping 20. */
void session_log_archive_crash(const char *report, size_t len);

#ifdef __cplusplus
}
#endif

#endif
