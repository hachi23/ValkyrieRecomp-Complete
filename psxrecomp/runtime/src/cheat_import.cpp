#include "cheat_import.h"

#include <cctype>
#include <cstdlib>
#include <map>
#include <sstream>

namespace psx {
namespace {

std::string trim(const std::string& s) {
    size_t a = 0, b = s.size();
    while (a < b && std::isspace(static_cast<unsigned char>(s[a]))) ++a;
    while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1]))) --b;
    return s.substr(a, b - a);
}

std::string unquote(std::string s) {
    s = trim(s);
    if (s.size() >= 2 && s.front() == '"' && s.back() == '"') s = s.substr(1, s.size() - 2);
    return s;
}

// "80012345 0063" in any of the shared spellings, or "" when not a code.
std::string normalize_code(const std::string& raw) {
    std::string hex;
    for (char c : trim(raw)) {
        if (std::isxdigit(static_cast<unsigned char>(c))) hex += static_cast<char>(std::toupper(c));
        else if (c != ' ' && c != '\t' && c != ':' && c != '-') return {};
    }
    if (hex.size() != 12) return {};
    return hex.substr(0, 8) + " " + hex.substr(8);
}

void push(std::vector<ImportedCheat>& out, ImportedCheat& current) {
    if (!current.codes.empty()) out.push_back(current);
    current = {};
}

std::vector<ImportedCheat> parse_retroarch(const std::vector<std::string>& lines) {
    std::map<int, ImportedCheat> by_index;
    for (const auto& line : lines) {
        const auto eq = line.find('=');
        if (line.rfind("cheat", 0) != 0 || eq == std::string::npos) continue;
        const std::string key = trim(line.substr(0, eq));
        const auto underscore = key.find('_');
        if (underscore == std::string::npos) continue;
        const int index = std::atoi(key.substr(5, underscore - 5).c_str());
        const std::string field = key.substr(underscore + 1);
        const std::string value = unquote(line.substr(eq + 1));
        if (field == "desc") {
            by_index[index].name = value;
        } else if (field == "code") {
            std::string part;
            std::istringstream parts(value);
            while (std::getline(parts, part, '+')) {
                const std::string code = normalize_code(part);
                if (!code.empty()) by_index[index].codes.push_back(code);
            }
        }
    }
    std::vector<ImportedCheat> out;
    for (auto& [index, cheat] : by_index)
        if (!cheat.codes.empty()) out.push_back(cheat);
    return out;
}

}  // namespace

std::vector<ImportedCheat> parse_cheat_text(const std::string& text,
                                            const std::string& fallback_name) {
    std::vector<std::string> lines;
    std::istringstream in(text);
    bool retroarch = false;
    for (std::string line; std::getline(in, line);) {
        line = trim(line);
        if (line.rfind("cheats", 0) == 0 && line.find('=') != std::string::npos) retroarch = true;
        lines.push_back(line);
    }
    if (retroarch) return parse_retroarch(lines);

    std::vector<ImportedCheat> out;
    ImportedCheat current;
    for (const auto& line : lines) {
        if (line.empty()) continue;
        const std::string code = normalize_code(line);
        if (!code.empty()) {
            if (current.name.empty())
                current.name = fallback_name.empty() ? "Imported cheat" : fallback_name;
            current.codes.push_back(code);
            continue;
        }
        if (line.front() == ';' || line.rfind("//", 0) == 0) continue;
        if (line.find('=') != std::string::npos && line.front() != '[') continue;
        std::string name = line;
        if (name.front() == '[' && name.back() == ']') name = name.substr(1, name.size() - 2);
        else if (name.front() == '#') name = name.substr(1);
        if (!current.codes.empty() || !current.name.empty()) push(out, current);
        current.name = trim(name);
    }
    push(out, current);
    return out;
}

}  // namespace psx
