#include "cheats.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { if (!(condition)) { \
    printf("FAIL line %d: %s\n", __LINE__, #condition); exit(1); \
} } while (0)

static unsigned char ram[0x200000];

static uint16_t read_ram(void *context, uint32_t offset, CheatsWidth width)
{
    unsigned char *bytes = (unsigned char *)context;
    CHECK(offset + width <= sizeof(ram));
    return width == CHEATS_WIDTH_16
        ? (uint16_t)(bytes[offset] | ((uint16_t)bytes[offset + 1] << 8))
        : bytes[offset];
}

static void write_ram(void *context, uint32_t offset, CheatsWidth width,
                      uint16_t value)
{
    unsigned char *bytes = (unsigned char *)context;
    CHECK(offset + width <= sizeof(ram));
    bytes[offset] = (unsigned char)value;
    if (width == CHEATS_WIDTH_16) bytes[offset + 1] = (unsigned char)(value >> 8);
}

static CheatsProgram *compile(const char *const *codes, size_t count)
{
    CheatsError error;
    CheatsProgram *program = cheats_compile(codes, count, sizeof(ram), &error);
    CHECK(program != NULL);
    CHECK(error.code == CHEATS_OK);
    CHECK(error.line == 0);
    return program;
}

static void apply(const char *const *codes, size_t count)
{
    CheatsMemory memory = {ram, read_ram, write_ram};
    CheatsProgram *program = compile(codes, count);
    cheats_apply(program, &memory);
    cheats_free(program);
}

static void writes_and_disable(void)
{
    const char *codes[] = {"  80000100 aBcD\t", "30000102 007f"};
    CheatsMemory memory = {ram, read_ram, write_ram};
    CheatsProgram *program = compile(codes, 2);
    cheats_apply(program, &memory);
    CHECK(read_ram(ram, 0x100, CHEATS_WIDTH_16) == 0xabcd);
    CHECK(ram[0x102] == 0x7f);
    write_ram(ram, 0x100, CHEATS_WIDTH_16, 0x1234);
    CHECK(read_ram(ram, 0x100, CHEATS_WIDTH_16) == 0x1234);
    cheats_apply(program, &memory);
    CHECK(read_ram(ram, 0x100, CHEATS_WIDTH_16) == 0xabcd);
    cheats_free(program);
}

static void conditionals(void)
{
    const char *conditions[] = {
        "D0000100 0005", "D1000100 0006", "D2000100 0006",
        "D3000100 0004", "E0000100 0005", "E1000100 0006"
    };
    size_t i;
    for (i = 0; i < sizeof(conditions) / sizeof(conditions[0]); ++i) {
        const char *codes[] = {conditions[i], "30000200 0077", "30000201 0088"};
        ram[0x100] = 5;
        ram[0x101] = 0;
        ram[0x200] = 0;
        apply(codes, 3);
        CHECK(ram[0x200] == 0x77);
        CHECK(ram[0x201] == 0x88);
        ram[0x100] = i == 0 || i == 4 ? 4 : i == 2 ? 6 : i == 3 ? 4 : 6;
        ram[0x200] = 0x11;
        ram[0x201] = 0;
        apply(codes, 3);
        CHECK(ram[0x200] == 0x11);
        CHECK(ram[0x201] == 0x88);
    }
    {
        const char *codes[] = {"D2000100 FFFF", "30000200 0099"};
        write_ram(ram, 0x100, CHEATS_WIDTH_16, 0x8000);
        apply(codes, 2);
        CHECK(ram[0x200] == 0x99);
    }
}

static void chained_conditions_and_repeats(void)
{
    const char *codes[] = {
        "D0000100 0001", "E0000102 0002", "50000302 0001",
        "80000200 FFFF", "30000208 0099"
    };
    ram[0x100] = 0;
    ram[0x101] = 0;
    ram[0x102] = 2;
    memset(ram + 0x200, 0x55, 8);
    apply(codes, 5);
    CHECK(read_ram(ram, 0x200, CHEATS_WIDTH_16) == 0x5555);
    CHECK(read_ram(ram, 0x202, CHEATS_WIDTH_16) == 0x5555);
    CHECK(read_ram(ram, 0x204, CHEATS_WIDTH_16) == 0x5555);
    CHECK(ram[0x208] == 0x99);
    ram[0x100] = 1;
    ram[0x102] = 0;
    apply(codes, 5);
    CHECK(read_ram(ram, 0x200, CHEATS_WIDTH_16) == 0x5555);
    ram[0x102] = 2;
    apply(codes, 5);
    CHECK(read_ram(ram, 0x200, CHEATS_WIDTH_16) == 0xffff);
    CHECK(read_ram(ram, 0x202, CHEATS_WIDTH_16) == 0);
    CHECK(read_ram(ram, 0x204, CHEATS_WIDTH_16) == 1);
    {
        const char *bytes[] = {"50000301 0002", "30000300 00FF"};
        apply(bytes, 2);
        CHECK(ram[0x300] == 255);
        CHECK(ram[0x301] == 1);
        CHECK(ram[0x302] == 3);
    }
}

static void reject(const char *const *codes, size_t count,
                   CheatsErrorCode expected, size_t line)
{
    CheatsError error;
    CheatsProgram *program = cheats_compile(codes, count, sizeof(ram), &error);
    CHECK(program == NULL);
    CHECK(error.code == expected);
    CHECK(error.line == line);
}

static void invalid_programs(void)
{
    const char *malformed[] = {"80000100 1234 trailing"};
    const char *short_code[] = {"80"};
    const char *unsupported[] = {"C0000100 0001"};
    const char *unsafe[] = {"80200000 0001"};
    const char *unaligned[] = {"80000101 0001"};
    const char *wide_byte[] = {"30000100 0100"};
    const char *orphan[] = {"D0000100 0001"};
    const char *repeat_orphan[] = {"50000302 0001"};
    const char *repeat_zero[] = {"50000002 0001", "80000100 0001"};
    const char *repeat_reserved[] = {"50010302 0001", "80000100 0001"};
    const char *repeat_condition[] = {"50000302 0001", "D0000100 0001"};
    const char *repeat_unsafe[] = {"50000302 0001", "801FFFFE 0001"};
    const char *repeat_odd[] = {"50000301 0001", "80000100 0001"};
    const char *atomic[] = {"30000100 0099", "invalid"};
    reject(malformed, 1, CHEATS_MALFORMED_CODE, 1);
    reject(short_code, 1, CHEATS_MALFORMED_CODE, 1);
    reject(unsupported, 1, CHEATS_UNSUPPORTED_OPCODE, 1);
    reject(unsafe, 1, CHEATS_UNSAFE_ADDRESS, 1);
    reject(unaligned, 1, CHEATS_UNALIGNED_ADDRESS, 1);
    reject(wide_byte, 1, CHEATS_INVALID_BYTE_VALUE, 1);
    reject(orphan, 1, CHEATS_ORPHAN_CONDITIONAL, 1);
    reject(repeat_orphan, 1, CHEATS_INVALID_REPEAT, 1);
    reject(repeat_zero, 2, CHEATS_INVALID_REPEAT, 1);
    reject(repeat_reserved, 2, CHEATS_INVALID_REPEAT, 1);
    reject(repeat_condition, 2, CHEATS_INVALID_REPEAT, 1);
    reject(repeat_unsafe, 2, CHEATS_UNSAFE_ADDRESS, 1);
    reject(repeat_odd, 2, CHEATS_UNALIGNED_ADDRESS, 1);
    ram[0x100] = 0x55;
    reject(atomic, 2, CHEATS_MALFORMED_CODE, 2);
    CHECK(ram[0x100] == 0x55);
    reject(NULL, 0, CHEATS_INVALID_ARGUMENT, 0);
    reject(malformed, 4097, CHEATS_TOO_MANY_CODES, 0);
}

int main(void)
{
    writes_and_disable();
    conditionals();
    chained_conditions_and_repeats();
    invalid_programs();
    puts("cheats_test passed");
    return 0;
}
