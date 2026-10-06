#include "cheat_catalog.h"
#include "psx_sha256.h"
#include "toml.hpp"
#include <algorithm>
#include <cctype>
#include <fstream>
#include <set>
#include <sstream>
#include <stdexcept>

namespace psx {
namespace {
constexpr size_t max_catalog_bytes = 1024 * 1024;
constexpr size_t max_entries = 512;
constexpr size_t max_codes = 1024;

std::string bounded_string(const toml::value& value, const char* key,
                           size_t bound, bool required) {
    if (!value.contains(key)) {
        if (required) throw std::runtime_error(std::string("Missing cheat ") + key);
        return {};
    }
    auto result = toml::find<std::string>(value, key);
    if (result.size() > bound || result.find('\0') != std::string::npos ||
        (required && result.empty()))
        throw std::runtime_error(std::string("Invalid cheat ") + key);
    return result;
}

bool valid_id(const std::string& id) {
    return !id.empty() && id.size() <= 128 && id.find('\0') == std::string::npos;
}
}

namespace {
std::unique_ptr<CheatsProgram, decltype(&cheats_free)> compile_codes(
        const std::vector<std::string>& codes, uint32_t ram_bytes, const std::string& label) {
    if (codes.empty() || codes.size() > max_codes)
        throw std::runtime_error("Invalid code count for " + label);
    std::vector<const char*> lines;
    for (const auto& code : codes) {
        if (code.size() > 64 || code.find('\0') != std::string::npos)
            throw std::runtime_error("Invalid code string for " + label);
        lines.push_back(code.c_str());
    }
    CheatsError compile_error{};
    std::unique_ptr<CheatsProgram, decltype(&cheats_free)> program(
        cheats_compile(lines.data(), lines.size(), ram_bytes, &compile_error), cheats_free);
    if (!program)
        throw std::runtime_error(label + " line " + std::to_string(compile_error.line) +
                                 ": " + cheats_error_message(compile_error.code));
    return program;
}

std::string sha256_hex(const std::string& bytes) {
    uint8_t digest[32];
    psx_sha256_compute(reinterpret_cast<const uint8_t*>(bytes.data()), bytes.size(), digest);
    std::string hash;
    constexpr char hex[] = "0123456789abcdef";
    for (uint8_t byte : digest) { hash += hex[byte >> 4]; hash += hex[byte & 15]; }
    return hash;
}

std::string toml_string(const std::string& value) {
    static const char hex[] = "0123456789abcdef";
    std::string out = "\"";
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
        else if (c < 0x20 || c == 0x7f) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += static_cast<char>(c);
    }
    return out + "\"";
}

std::string slug(const std::string& name) {
    std::string out;
    for (unsigned char c : name) {
        if (std::isalnum(c)) out += static_cast<char>(std::tolower(c));
        else if (!out.empty() && out.back() != '-') out += '-';
        if (out.size() >= 48) break;
    }
    while (!out.empty() && out.back() == '-') out.pop_back();
    return out.empty() ? "cheat" : out;
}
}

bool CheatSession::load_catalog(const std::filesystem::path& path,
                               uint32_t ram_bytes, std::string& error) {
    error.clear();
    try {
        std::ifstream file(path, std::ios::binary);
        if (!file) throw std::runtime_error("Cannot open cheat catalog " + path.string());
        std::string bytes(max_catalog_bytes + 1, '\0');
        file.read(bytes.data(), static_cast<std::streamsize>(bytes.size()));
        const auto size = static_cast<size_t>(file.gcount());
        if (size > max_catalog_bytes) throw std::runtime_error("Cheat catalog exceeds 1 MiB");
        if (file.bad()) throw std::runtime_error("Cannot read cheat catalog");
        bytes.resize(size);
        std::istringstream input(bytes);
        const auto doc = toml::parse(input, path.string());
        if (!doc.is_table()) throw std::runtime_error("Cheat catalog must be a table");
        for (const auto& item : doc.as_table())
            if (item.first != "cheat" && item.first != "disc_serial")
                throw std::runtime_error("Unknown catalog field " + item.first);
        std::string serial = bounded_string(doc, "disc_serial", 32, false);
        std::vector<CheatCatalogEntry> parsed;
        std::set<std::string> identifiers;
        if (doc.contains("cheat")) {
            const auto& entries = toml::find(doc, "cheat").as_array();
            if (entries.size() > max_entries) throw std::runtime_error("Too many catalog cheats");
            for (const auto& value : entries) {
                if (!value.is_table()) throw std::runtime_error("Cheat entry must be a table");
                for (const auto& item : value.as_table())
                    if (item.first != "id" && item.first != "name" && item.first != "codes" &&
                        item.first != "notes" && item.first != "source" && item.first != "tested")
                        throw std::runtime_error("Unknown cheat field " + item.first);
                CheatCatalogEntry row;
                row.id = bounded_string(value, "id", 128, true);
                row.name = bounded_string(value, "name", 256, true);
                row.notes = bounded_string(value, "notes", 4096, false);
                row.source = bounded_string(value, "source", 2048, false);
                if (!identifiers.insert(row.id).second)
                    throw std::runtime_error("Duplicate cheat id " + row.id);
                if (value.contains("tested")) row.tested = toml::find<bool>(value, "tested");
                row.codes = toml::find<std::vector<std::string>>(value, "codes");
                row.program = compile_codes(row.codes, ram_bytes, row.id);
                parsed.push_back(std::move(row));
            }
        }
        rows_ = std::move(parsed);
        hash_ = sha256_hex(bytes);
        serial_ = std::move(serial);
        ram_bytes_ = ram_bytes;
        changed("catalog");
        return true;
    } catch (const std::exception& e) {
        error = e.what();
        return false;
    }
}

CheatAddResult CheatSession::add_cheats(const std::vector<ImportedCheat>& cheats) {
    CheatAddResult result;
    for (const auto& cheat : cheats) {
        const bool duplicate = std::any_of(rows_.begin(), rows_.end(),
            [&](const CheatCatalogEntry& row) { return row.codes == cheat.codes; });
        if (duplicate) { ++result.duplicates; continue; }
        if (rows_.size() >= max_entries) { result.errors.push_back("Cheat list is full"); break; }
        CheatCatalogEntry row;
        row.name = cheat.name.substr(0, 256);
        try {
            row.program = compile_codes(cheat.codes, ram_bytes_, row.name);
        } catch (const std::exception& e) {
            result.errors.push_back(e.what());
            continue;
        }
        row.codes = cheat.codes;
        row.notes = "Added by you.";
        const std::string base = slug(row.name);
        row.id = base;
        for (int n = 2; std::any_of(rows_.begin(), rows_.end(),
                 [&](const CheatCatalogEntry& r) { return r.id == row.id; }); ++n)
            row.id = base + "-" + std::to_string(n);
        rows_.push_back(std::move(row));
        ++result.added;
    }
    if (result.added) changed("catalog");
    return result;
}

bool CheatSession::remove_cheat(const std::string& id) {
    const auto it = std::find_if(rows_.begin(), rows_.end(),
                                 [&](const CheatCatalogEntry& row) { return row.id == id; });
    if (it == rows_.end()) return false;
    rows_.erase(it);
    selected_.erase(std::remove(selected_.begin(), selected_.end(), id), selected_.end());
    changed("catalog");
    return true;
}

void CheatSession::clear_cheats() {
    rows_.clear();
    selected_.clear();
    changed("catalog");
}

bool CheatSession::save_catalog(const std::filesystem::path& path, std::string& error) {
    std::ostringstream out;
    if (!serial_.empty()) out << "disc_serial = " << toml_string(serial_) << "\n";
    for (const auto& row : rows_) {
        out << "\n[[cheat]]\nid = " << toml_string(row.id) << "\nname = " << toml_string(row.name)
            << "\ncodes = [";
        for (size_t i = 0; i < row.codes.size(); ++i)
            out << (i ? ", " : "") << toml_string(row.codes[i]);
        out << "]\n";
        if (!row.notes.empty()) out << "notes = " << toml_string(row.notes) << "\n";
        if (!row.source.empty()) out << "source = " << toml_string(row.source) << "\n";
        out << "tested = " << (row.tested ? "true" : "false") << "\n";
    }
    const std::string bytes = out.str();
    const auto tmp = std::filesystem::path(path.string() + ".tmp");
    {
        std::ofstream file(tmp, std::ios::binary | std::ios::trunc);
        if (!file || !(file << bytes) || !file.flush()) {
            error = "Cannot write " + tmp.string();
            return false;
        }
    }
    std::error_code ec;
    std::filesystem::rename(tmp, path, ec);
    if (ec) { error = "Cannot replace " + path.string() + ": " + ec.message(); return false; }
    hash_ = sha256_hex(bytes);
    return true;
}

bool CheatSession::is_selected(const std::string& id) const {
    return std::find(selected_.begin(), selected_.end(), id) != selected_.end();
}

std::vector<std::string> CheatSession::effective_ids() const {
    std::vector<std::string> ids;
    if (writes_enabled())
        for (const auto& row : rows_) if (is_selected(row.id)) ids.push_back(row.id);
    return ids;
}

bool CheatSession::set_selected(const std::vector<std::string>& ids) {
    if (ids.size() > max_entries) return false;
    std::vector<std::string> normalized;
    for (const auto& id : ids) {
        if (!valid_id(id)) return false;
        if (std::find(normalized.begin(), normalized.end(), id) == normalized.end())
            normalized.push_back(id);
    }
    if (selected_ != normalized) { selected_ = std::move(normalized); changed("selection"); }
    return true;
}

bool CheatSession::set_enabled(const std::string& id, bool enabled) {
    if (!valid_id(id)) return false;
    auto ids = selected_;
    ids.erase(std::remove(ids.begin(), ids.end(), id), ids.end());
    if (enabled) ids.push_back(id);
    return set_selected(ids);
}

void CheatSession::disable_all() { set_selected({}); }

void CheatSession::set_gates(bool assist, bool safe, bool netplay) {
    if (assist_ == assist && safe_ == safe && netplay_ == netplay) return;
    assist_ = assist; safe_ = safe; netplay_ = netplay;
    changed("gates");
}

void CheatSession::apply(const CheatsMemory& memory) const {
    if (writes_enabled())
        for (const auto& row : rows_)
            if (is_selected(row.id)) cheats_apply(row.program.get(), &memory);
}

void CheatSession::changed(const char* reason) const {
    if (callback_) callback_(context_, reason);
}
}
