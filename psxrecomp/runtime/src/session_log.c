#include "session_log.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <direct.h>
#include <windows.h>
#define SL_MKDIR(p) _mkdir(p)
#else
#include <dirent.h>
#include <sys/stat.h>
#define SL_MKDIR(p) mkdir((p), 0755)
#endif

extern uint64_t s_frame_count;

#define SL_KEEP_SESSIONS 10
#define SL_KEEP_CRASHES 20
#define SL_KEEP_FREEZE_DUMPS 3   /* 30-130 MB each */
#define SL_MAX_LISTED 256
#define SL_CHEAT_RING 32
#define SL_CHEAT_WINDOW_FRAMES 600

static FILE *s_log;
static char s_dir[512];
static char s_path[640];
static char s_marker[640];
static char s_header[2048];
static char s_cheats[1024] = "";
static char s_previous[1400];
static int s_have_previous;
static int s_last_load_slot = -1;
static uint64_t s_last_load_frame;

typedef struct { uint64_t frame; char csv[256]; } CheatChange;
static CheatChange s_ring[SL_CHEAT_RING];
static unsigned s_ring_n;

static int cmp_names(const void *a, const void *b) {
    return strcmp(*(char *const *)a, *(char *const *)b);
}

/* Delete the oldest prefix*suffix files in dir beyond keep (names sort by time). */
static void prune(const char *dir, const char *prefix, const char *suffix, int keep) {
    char *names[SL_MAX_LISTED];
    int n = 0;
    size_t plen = strlen(prefix), slen = strlen(suffix);
#ifdef _WIN32
    char pattern[600];
    WIN32_FIND_DATAA fd;
    snprintf(pattern, sizeof(pattern), "%s\\%s*%s", dir, prefix, suffix);
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h == INVALID_HANDLE_VALUE) return;
    do {
        if (n < SL_MAX_LISTED) names[n++] = _strdup(fd.cFileName);
    } while (FindNextFileA(h, &fd));
    FindClose(h);
#else
    DIR *d = opendir(dir);
    struct dirent *e;
    if (!d) return;
    while ((e = readdir(d)) && n < SL_MAX_LISTED) {
        size_t len = strlen(e->d_name);
        if (len > plen + slen && !strncmp(e->d_name, prefix, plen) &&
            !strcmp(e->d_name + len - slen, suffix))
            names[n++] = strdup(e->d_name);
    }
    closedir(d);
#endif
    qsort(names, (size_t)n, sizeof(names[0]), cmp_names);
    for (int i = 0; i < n; i++) {
        if (i < n - keep) {
            char path[900];
            snprintf(path, sizeof(path), "%s/%s", dir, names[i]);
            remove(path);
        }
        free(names[i]);
    }
}

static void stamp(char *out, size_t cap, const char *fmt) {
    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    if (!tm || !strftime(out, cap, fmt, tm)) snprintf(out, cap, "unknown");
}

static void write_marker(void) {
    FILE *f;
    if (!s_marker[0]) return;
    f = fopen(s_marker, "w");
    if (!f) return;
    fprintf(f, "session=%s\ncheats=%s\n", s_path, s_cheats[0] ? s_cheats : "none");
    fclose(f);
}

static void read_previous_marker(void) {
    char line[700], session[640] = "", cheats[700] = "none";
    FILE *f = fopen(s_marker, "r");
    if (!f) return;
    while (fgets(line, sizeof(line), f)) {
        line[strcspn(line, "\r\n")] = '\0';
        if (!strncmp(line, "session=", 8)) snprintf(session, sizeof(session), "%s", line + 8);
        else if (!strncmp(line, "cheats=", 7)) snprintf(cheats, sizeof(cheats), "%s", line + 7);
    }
    fclose(f);
    snprintf(s_previous, sizeof(s_previous),
             "Cheats that were on: %s.\nSession log: %s", cheats, session);
    s_have_previous = 1;
}

void session_log_open(const char *logs_dir) {
    char name[64], crashes[600];
    if (s_log || !logs_dir) return;
    snprintf(s_dir, sizeof(s_dir), "%s", logs_dir);
    SL_MKDIR(s_dir);
    snprintf(crashes, sizeof(crashes), "%s/crashes", s_dir);
    SL_MKDIR(crashes);
    snprintf(s_marker, sizeof(s_marker), "%s/running.txt", s_dir);
    read_previous_marker();
    stamp(name, sizeof(name), "session-%Y%m%d-%H%M%S.log");
    snprintf(s_path, sizeof(s_path), "%s/%s", s_dir, name);
    s_log = fopen(s_path, "w");
    prune(s_dir, "session-", ".log", SL_KEEP_SESSIONS);
    prune(s_dir, "psx_freeze_dump_", ".json", SL_KEEP_FREEZE_DUMPS);
    write_marker();
    if (s_have_previous)
        session_log_event("previous run ended without a clean exit (%s)", s_previous);
}

void session_log_event(const char *fmt, ...) {
    char msg[1024], when[32];
    va_list ap;
    if (!s_log) return;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof(msg), fmt, ap);
    va_end(ap);
    stamp(when, sizeof(when), "%H:%M:%S");
    fprintf(s_log, "[%s] f=%llu %s\n", when, (unsigned long long)s_frame_count, msg);
    fflush(s_log);
    if (s_frame_count == 0) {
        size_t used = strlen(s_header);
        snprintf(s_header + used, sizeof(s_header) - used, "%s\n", msg);
    }
}

void session_log_set_active_cheats(const char *csv) {
    CheatChange *c;
    if (!csv) csv = "";
    if (!strcmp(csv, s_cheats)) return;
    snprintf(s_cheats, sizeof(s_cheats), "%s", csv);
    c = &s_ring[s_ring_n++ % SL_CHEAT_RING];
    c->frame = s_frame_count;
    snprintf(c->csv, sizeof(c->csv), "%s", csv);
    session_log_event("cheats active: %s", csv[0] ? csv : "none");
    write_marker();
}

void session_log_note_state_load(int slot) {
    s_last_load_slot = slot;
    s_last_load_frame = s_frame_count;
    session_log_event("loaded save state slot %d", slot + 1);
}

void session_log_close(void) {
    if (!s_log) return;
    session_log_event("clean exit");
    fclose(s_log);
    s_log = NULL;
    if (s_marker[0]) remove(s_marker);
}

const char *session_log_path(void) { return s_path; }

const char *session_log_dir(void) { return s_dir; }

const char *session_log_previous_crash(void) { return s_have_previous ? s_previous : NULL; }

static size_t append_escaped(char *out, size_t cap, size_t pos, const char *s) {
    for (; *s && pos + 7 < cap; s++) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') { out[pos++] = '\\'; out[pos++] = (char)c; }
        else if (c == '\n') { out[pos++] = '\\'; out[pos++] = 'n'; }
        else if (c >= 0x20) out[pos++] = (char)c;
    }
    out[pos] = '\0';
    return pos;
}

size_t session_log_crash_json(char *out, size_t cap) {
    size_t pos = 0;
    unsigned first, i;
    int any = 0;
    if (!out || cap < 64) return 0;
#define SL_LIT(t) pos += (size_t)snprintf(out + pos, cap - pos, "%s", (t))
    SL_LIT("\"session_log\": \"");
    pos = append_escaped(out, cap, pos, s_path);
    SL_LIT("\",\n  \"active_cheats\": \"");
    pos = append_escaped(out, cap, pos, s_cheats);
    SL_LIT("\",\n  \"startup\": \"");
    pos = append_escaped(out, cap, pos, s_header);
    pos += (size_t)snprintf(out + pos, cap - pos,
                            "\",\n  \"last_state_load\": {\"slot\": %d, \"frame\": %llu},\n"
                            "  \"cheat_changes_last_600_frames\": [",
                            s_last_load_slot < 0 ? 0 : s_last_load_slot + 1,
                            (unsigned long long)s_last_load_frame);
    first = s_ring_n > SL_CHEAT_RING ? s_ring_n - SL_CHEAT_RING : 0;
    for (i = first; i < s_ring_n && pos + 300 < cap; i++) {
        const CheatChange *c = &s_ring[i % SL_CHEAT_RING];
        if (c->frame + SL_CHEAT_WINDOW_FRAMES < s_frame_count) continue;
        pos += (size_t)snprintf(out + pos, cap - pos, "%s{\"frame\": %llu, \"cheats\": \"",
                                any ? ", " : "", (unsigned long long)c->frame);
        pos = append_escaped(out, cap, pos, c->csv);
        SL_LIT("\"}");
        any = 1;
    }
    SL_LIT("]");
#undef SL_LIT
    return pos < cap ? pos : cap - 1;
}

void session_log_archive_crash(const char *report, size_t len) {
    char name[64], path[700], crashes[600];
    FILE *f;
    if (!s_dir[0] || !report) return;
    snprintf(crashes, sizeof(crashes), "%s/crashes", s_dir);
    stamp(name, sizeof(name), "crash-%Y%m%d-%H%M%S.json");
    snprintf(path, sizeof(path), "%s/%s", crashes, name);
    f = fopen(path, "wb");
    if (!f) return;
    fwrite(report, 1, len, f);
    fclose(f);
    session_log_event("crash report saved to %s", path);
    prune(crashes, "crash-", ".json", SL_KEEP_CRASHES);
}
