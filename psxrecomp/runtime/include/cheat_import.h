#pragma once

#include <string>
#include <vector>

namespace psx {

struct ImportedCheat {
    std::string name;
    std::vector<std::string> codes;  // normalized "AAAAAAAA VVVV"
};

// Reads the cheat text people share: RetroArch .cht (cheatN_desc/cheatN_code),
// [Name] blocks (PCSX, ePSXe, DuckStation; key = value lines ignored), and
// plain pastes where a non-code line names the codes under it. Codes may be
// written "80012345 0063", "800123450063" or "80012345:0063". Cheats with no
// codes are dropped; unnamed codes are named after fallback_name.
std::vector<ImportedCheat> parse_cheat_text(const std::string& text,
                                            const std::string& fallback_name);

}
