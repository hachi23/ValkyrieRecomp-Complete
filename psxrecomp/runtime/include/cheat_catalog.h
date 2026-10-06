#pragma once

#include "cheats.h"
#include "cheat_import.h"
#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace psx {

struct CheatCatalogEntry {
    std::string id;
    std::string name;
    std::vector<std::string> codes;
    std::string notes;
    std::string source;
    bool tested = false;
    std::unique_ptr<CheatsProgram, decltype(&cheats_free)> program{nullptr, cheats_free};
};

struct CheatAddResult {
    int added = 0;
    int duplicates = 0;
    std::vector<std::string> errors;
};

class CheatSession {
public:
    using EventCallback = void (*)(void*, const char*);
    bool load_catalog(const std::filesystem::path& path, uint32_t ram_bytes,
                      std::string& error);
    const std::vector<CheatCatalogEntry>& rows() const { return rows_; }
    const std::string& catalog_hash() const { return hash_; }
    const std::string& disc_serial() const { return serial_; }
    const std::vector<std::string>& selected_ids() const { return selected_; }
    std::vector<std::string> effective_ids() const;
    bool set_selected(const std::vector<std::string>& ids);
    // Editing: compiled before they are kept; duplicates of existing codes skipped.
    CheatAddResult add_cheats(const std::vector<ImportedCheat>& cheats);
    bool remove_cheat(const std::string& id);
    void clear_cheats();
    bool save_catalog(const std::filesystem::path& path, std::string& error);
    bool set_enabled(const std::string& id, bool enabled);
    void disable_all();
    void set_gates(bool assist, bool safe, bool netplay);
    bool assist_enabled() const { return assist_; }
    bool safe_mode() const { return safe_; }
    bool writes_enabled() const { return assist_ && !safe_ && !netplay_; }
    bool is_selected(const std::string& id) const;
    void apply(const CheatsMemory& memory) const;
    void set_event_callback(EventCallback callback, void* context) {
        callback_ = callback; context_ = context;
    }
private:
    void changed(const char* reason) const;
    std::vector<CheatCatalogEntry> rows_;
    std::vector<std::string> selected_;
    std::string hash_;
    std::string serial_;
    uint32_t ram_bytes_ = 0x200000u;
    bool assist_ = false;
    bool safe_ = false;
    bool netplay_ = false;
    EventCallback callback_ = nullptr;
    void* context_ = nullptr;
};

}

psx::CheatSession& psx_cheats_session();
bool psx_cheats_load(const std::filesystem::path& path, std::string& error);
bool psx_cheats_verify_serial(const std::string& disc_serial, std::string& error);
