#include "cheat_import.h"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#define CHECK(condition) do { if (!(condition)) { \
    std::printf("FAIL line %d: %s\n", __LINE__, #condition); std::exit(1); \
} } while (0)

using psx::parse_cheat_text;

static void retroarch_cht() {
    const auto cheats = parse_cheat_text(
        "cheats = 2\n\n"
        "cheat0_desc = \"Infinite HP\"\n"
        "cheat0_code = \"8001e2a4 03e7+8001E2A6 03E7\"\n"
        "cheat0_enable = false\n"
        "cheat1_desc = \"Max Gold\"\n"
        "cheat1_code = \"80050000 FFFF\"\n", "Pasted");
    CHECK(cheats.size() == 2);
    CHECK(cheats[0].name == "Infinite HP");
    CHECK((cheats[0].codes == std::vector<std::string>{"8001E2A4 03E7", "8001E2A6 03E7"}));
    CHECK(cheats[1].name == "Max Gold");
    CHECK((cheats[1].codes == std::vector<std::string>{"80050000 FFFF"}));
}

static void bracket_blocks_with_keys() {
    const auto cheats = parse_cheat_text(
        "[Infinite Items]\n"
        "Type = Gameshark\n"
        "Activation = EndFrame\n"
        "D005A7BC FFFF\n"
        "8005A7BC 0000\n"
        "\n"
        "[No Codes Here]\n"
        "[Walk Through Walls]\n"
        "800A1234:2400\n", "Pasted");
    CHECK(cheats.size() == 2);
    CHECK(cheats[0].name == "Infinite Items");
    CHECK((cheats[0].codes == std::vector<std::string>{"D005A7BC FFFF", "8005A7BC 0000"}));
    CHECK(cheats[1].name == "Walk Through Walls");
    CHECK((cheats[1].codes == std::vector<std::string>{"800A1234 2400"}));
}

static void plain_paste() {
    const auto cheats = parse_cheat_text(
        "Valkyrie Profile (USA)\n"
        "Max Materialize Points\n"
        "800E4A2C 270F\n"
        "#Have All Items\n"
        "50006402 0000\n"
        "3008C3E8 0063\n", "Pasted");
    CHECK(cheats.size() == 2);
    CHECK(cheats[0].name == "Max Materialize Points");
    CHECK(cheats[1].name == "Have All Items");
    CHECK((cheats[1].codes == std::vector<std::string>{"50006402 0000", "3008C3E8 0063"}));
}

static void bare_codes_use_fallback_name() {
    const auto cheats = parse_cheat_text("800e4a2c270f\n", "My cheat");
    CHECK(cheats.size() == 1);
    CHECK(cheats[0].name == "My cheat");
    CHECK((cheats[0].codes == std::vector<std::string>{"800E4A2C 270F"}));
}

static void rejects_non_codes() {
    CHECK(parse_cheat_text("hello\nworld\n8001234 0063\n", "x").empty());
    CHECK(parse_cheat_text("", "x").empty());
}

int main() {
    retroarch_cht();
    bracket_blocks_with_keys();
    plain_paste();
    bare_codes_use_fallback_name();
    rejects_non_codes();
    std::puts("cheat_import_test passed");
    return 0;
}
