#include "cheat_catalog.h"

#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>

#define CHECK(condition) do { if (!(condition)) { \
    std::printf("FAIL line %d: %s\n", __LINE__, #condition); std::exit(1); \
} } while (0)

namespace fs = std::filesystem;

int main() {
    const fs::path dir = fs::temp_directory_path() / "psx_cheat_catalog_test";
    fs::remove_all(dir);
    fs::create_directories(dir);
    const fs::path path = dir / "SLUS-01156.toml";
    std::ofstream(path) << "disc_serial = \"SLUS-01156\"\n\n[[cheat]]\nid = \"battle-item-use\"\n"
                           "name = \"Infinite item use\"\ncodes = [\"D005A7BC FFFF\", \"8005A7BC 0000\"]\n"
                           "notes = \"Bundled\"\ntested = true\n";

    psx::CheatSession session;
    std::string error;
    CHECK(session.load_catalog(path, 0x200000u, error));
    session.set_selected({"battle-item-use"});

    const auto added = session.add_cheats(psx::parse_cheat_text(
        "[Max Gold]\n80050000 FFFF\n"
        "[Same codes as bundled]\nD005A7BC FFFF\n8005A7BC 0000\n"
        "[Bad opcode]\n90050000 0001\n"
        "[Max Gold]\n80050002 FFFF\n", "x"));
    CHECK(added.added == 2);
    CHECK(added.duplicates == 1);
    CHECK(added.errors.size() == 1);
    CHECK(added.errors[0] == "Bad opcode line 1: Unsupported GameShark opcode");
    CHECK(session.rows().size() == 3);
    CHECK(session.rows()[1].id == "max-gold");
    CHECK(session.rows()[2].id == "max-gold-2");

    CHECK(session.remove_cheat("battle-item-use"));
    CHECK(session.selected_ids().empty());
    CHECK(!session.remove_cheat("battle-item-use"));
    CHECK(session.save_catalog(path, error));

    psx::CheatSession reloaded;
    CHECK(reloaded.load_catalog(path, 0x200000u, error));
    CHECK(reloaded.disc_serial() == "SLUS-01156");
    CHECK(reloaded.rows().size() == 2);
    CHECK(reloaded.rows()[0].name == "Max Gold");
    CHECK((reloaded.rows()[1].codes == std::vector<std::string>{"80050002 FFFF"}));
    CHECK(reloaded.rows()[1].notes == "Added by you.");

    reloaded.clear_cheats();
    CHECK(reloaded.rows().empty());
    fs::remove_all(dir);
    std::puts("cheat_catalog_test passed");
    return 0;
}
