#include "ra_host.h"
#include "cheat_catalog.h"
#include "session_log.h"

#include <cstdint>
#include <algorithm>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

extern "C" uint16_t psx_read_half(uint32_t addr);
extern "C" uint8_t  psx_read_byte(uint32_t addr);
extern "C" void     psx_write_half(uint32_t addr, uint16_t val);
extern "C" void     psx_write_byte(uint32_t addr, uint8_t val);
extern "C" int      psx_netplay_active(void);
extern "C" void     debug_server_send_fmt(const char *fmt, ...);

namespace {

constexpr uint32_t kRamBase = 0x80000000u;

psx::CheatSession g_session;
bool g_catalog_loaded = false;

uint16_t read_ram(void *, uint32_t offset, CheatsWidth width) {
    return width == CHEATS_WIDTH_16 ? psx_read_half(kRamBase | offset)
                                    : psx_read_byte(kRamBase | offset);
}

void write_ram(void *, uint32_t offset, CheatsWidth width, uint16_t value) {
    if (width == CHEATS_WIDTH_16) psx_write_half(kRamBase | offset, value);
    else psx_write_byte(kRamBase | offset, static_cast<uint8_t>(value));
}

const CheatsMemory kMemory = {nullptr, read_ram, write_ram};

void append_json_string(std::string &out, const std::string &value) {
    static const char hex[] = "0123456789abcdef";
    out += '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
        else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += static_cast<char>(c);
    }
    out += '"';
}

}  // namespace

psx::CheatSession &psx_cheats_session() { return g_session; }

static void log_active_cheats(void *, const char *) {
    std::string csv;
    for (const auto &id : g_session.effective_ids()) csv += (csv.empty() ? "" : ",") + id;
    session_log_set_active_cheats(csv.c_str());
}

bool psx_cheats_load(const std::filesystem::path &path, std::string &error) {
    g_catalog_loaded = g_session.load_catalog(path, 0x200000u, error);
    if (g_catalog_loaded) g_session.set_event_callback(log_active_cheats, nullptr);
    return g_catalog_loaded;
}

bool psx_cheats_verify_serial(const std::string &disc_serial, std::string &error) {
    if (!g_catalog_loaded) return false;
    if (!g_session.disc_serial().empty() && g_session.disc_serial() != disc_serial) {
        error = "catalog is for " + g_session.disc_serial() + ", running disc is " + disc_serial;
        g_catalog_loaded = false;
        return false;
    }
    session_log_event("cheat catalog for %s, sha256 %s, %zu cheats", disc_serial.c_str(),
                      g_session.catalog_hash().c_str(), g_session.rows().size());
    return true;
}

extern "C" void psx_cheats_on_vblank(void) {
    if (!g_catalog_loaded) return;
    /* RetroAchievements hardcore forbids memory edits; it shares the netplay gate. */
    g_session.set_gates(g_session.assist_enabled(), g_session.safe_mode(),
                        psx_netplay_active() != 0 || ra_hardcore_active() != 0);
    g_session.apply(kMemory);
}

extern "C" void psx_cheats_debug_status(int id) {
    std::string out = "{\"id\":" + std::to_string(id) + ",\"ok\":true,\"loaded\":";
    out += g_catalog_loaded ? "true" : "false";
    out += ",\"assist\":";
    out += g_session.assist_enabled() ? "true" : "false";
    out += ",\"safe_mode\":";
    out += g_session.safe_mode() ? "true" : "false";
    out += ",\"writes_enabled\":";
    out += g_session.writes_enabled() ? "true" : "false";
    out += ",\"catalog_hash\":";
    append_json_string(out, g_session.catalog_hash());
    out += ",\"cheats\":[";
    bool first = true;
    for (const auto &row : g_session.rows()) {
        if (!first) out += ',';
        first = false;
        out += "{\"id\":";
        append_json_string(out, row.id);
        out += ",\"name\":";
        append_json_string(out, row.name);
        out += ",\"tested\":";
        out += row.tested ? "true" : "false";
        out += ",\"selected\":";
        out += g_session.is_selected(row.id) ? "true" : "false";
        out += '}';
    }
    out += "]}";
    debug_server_send_fmt("%s", out.c_str());
}

extern "C" int psx_cheats_debug_set(const char *cheat_id, int enabled) {
    if (!g_catalog_loaded || !cheat_id) return 0;
    for (const auto &row : g_session.rows())
        if (row.id == cheat_id) return g_session.set_enabled(row.id, enabled != 0) ? 1 : 0;
    return 0;
}

extern "C" void psx_cheats_debug_set_assist(int enabled) {
    g_session.set_gates(enabled != 0, g_session.safe_mode(), psx_netplay_active() != 0);
}

namespace {
std::vector<std::string> active_ids() {
    auto ids = g_catalog_loaded ? g_session.effective_ids() : std::vector<std::string>{};
    std::sort(ids.begin(), ids.end());
    return ids;
}
}  // namespace

extern "C" void psx_cheats_write_state_sidecar(const char *path) {
    std::ofstream out(path, std::ios::trunc);
    for (const auto &id : active_ids()) out << id << '\n';
}

/* 0 = no sidecar or same cheats; otherwise writes a toast into msg. */
extern "C" int psx_cheats_check_state_sidecar(const char *path, char *msg, size_t cap) {
    std::ifstream in(path);
    if (!in) return 0;
    std::vector<std::string> saved;
    for (std::string line; std::getline(in, line);)
        if (!line.empty()) saved.push_back(line);
    std::sort(saved.begin(), saved.end());
    const auto now = active_ids();
    if (saved == now) return 0;
    std::snprintf(msg, cap, "Save state used different cheats (%zu then, %zu now)",
                  saved.size(), now.size());
    return 1;
}
