#include "cheats.h"

#include <ctype.h>
#include <stdlib.h>

#define CHEATS_MAX_CODES 4096u

typedef enum OperationKind {
    OP_WRITE,
    OP_EQUAL,
    OP_NOT_EQUAL,
    OP_LESS,
    OP_GREATER
} OperationKind;

typedef struct Operation {
    OperationKind kind;
    CheatsWidth width;
    uint32_t address;
    uint16_t value;
    uint16_t increment;
    uint8_t repeat;
    uint8_t stride;
    size_t false_next;
    size_t source_line;
} Operation;

struct CheatsProgram {
    size_t count;
    Operation operations[];
};

static int hex_digit(unsigned char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int parse_line(const char *text, uint32_t *first, uint16_t *second)
{
    uint32_t a = 0, b = 0;
    size_t i;
    if (!text) return 0;
    while (isspace((unsigned char)*text)) ++text;
    for (i = 0; i < 8; ++i) {
        int digit = hex_digit((unsigned char)*text);
        if (digit < 0) return 0;
        a = (a << 4) | (uint32_t)digit;
        ++text;
    }
    if (!isspace((unsigned char)*text)) return 0;
    while (isspace((unsigned char)*text)) ++text;
    for (i = 0; i < 4; ++i) {
        int digit = hex_digit((unsigned char)*text);
        if (digit < 0) return 0;
        b = (b << 4) | (uint32_t)digit;
        ++text;
    }
    while (isspace((unsigned char)*text)) ++text;
    if (*text) return 0;
    *first = a;
    *second = (uint16_t)b;
    return 1;
}

static CheatsErrorCode decode(uint32_t first, uint16_t value, Operation *op)
{
    unsigned opcode = first >> 24;
    op->address = first & 0xffffffu;
    op->value = value;
    op->repeat = 1;
    switch (opcode) {
    case 0x80: op->kind = OP_WRITE; op->width = CHEATS_WIDTH_16; break;
    case 0x30: op->kind = OP_WRITE; op->width = CHEATS_WIDTH_8; break;
    case 0xd0: op->kind = OP_EQUAL; op->width = CHEATS_WIDTH_16; break;
    case 0xd1: op->kind = OP_NOT_EQUAL; op->width = CHEATS_WIDTH_16; break;
    case 0xd2: op->kind = OP_LESS; op->width = CHEATS_WIDTH_16; break;
    case 0xd3: op->kind = OP_GREATER; op->width = CHEATS_WIDTH_16; break;
    case 0xe0: op->kind = OP_EQUAL; op->width = CHEATS_WIDTH_8; break;
    case 0xe1: op->kind = OP_NOT_EQUAL; op->width = CHEATS_WIDTH_8; break;
    default: return CHEATS_UNSUPPORTED_OPCODE;
    }
    if (op->width == CHEATS_WIDTH_8 && value > 255)
        return CHEATS_INVALID_BYTE_VALUE;
    return CHEATS_OK;
}

static CheatsErrorCode validate_address(const Operation *op, uint32_t ram_bytes)
{
    uint32_t last = op->address + (uint32_t)(op->repeat - 1) * op->stride;
    if (last >= ram_bytes || (uint32_t)op->width > ram_bytes - last)
        return CHEATS_UNSAFE_ADDRESS;
    if (op->width == CHEATS_WIDTH_16 &&
        ((op->address & 1u) || (op->repeat > 1 && (op->stride & 1u))))
        return CHEATS_UNALIGNED_ADDRESS;
    return CHEATS_OK;
}

CheatsProgram *cheats_compile(const char *const *codes, size_t count,
                             uint32_t ram_bytes, CheatsError *error)
{
    CheatsProgram *program = NULL;
    CheatsErrorCode failure = CHEATS_OK;
    size_t line = 0, i;
    if (!codes || !count || !ram_bytes || ram_bytes > 0x1000000u) {
        failure = CHEATS_INVALID_ARGUMENT;
        goto failed;
    }
    if (count > CHEATS_MAX_CODES) {
        failure = CHEATS_TOO_MANY_CODES;
        goto failed;
    }
    program = (CheatsProgram *)calloc(1, sizeof(*program) + count * sizeof(Operation));
    if (!program) {
        failure = CHEATS_OUT_OF_MEMORY;
        goto failed;
    }
    for (i = 0; i < count; ++i) {
        uint32_t first;
        uint16_t value;
        Operation *op = &program->operations[program->count];
        line = i + 1;
        op->source_line = line;
        if (!parse_line(codes[i], &first, &value)) {
            failure = CHEATS_MALFORMED_CODE;
            goto failed;
        }
        if ((first >> 24) == 0x50) {
            uint32_t write_first;
            uint16_t write_value;
            uint8_t repeat = (uint8_t)(first >> 8);
            if ((first & 0x00ff0000u) || !repeat || ++i >= count) {
                failure = CHEATS_INVALID_REPEAT;
                goto failed;
            }
            if (!parse_line(codes[i], &write_first, &write_value)) {
                line = i + 1;
                failure = CHEATS_MALFORMED_CODE;
                goto failed;
            }
            failure = decode(write_first, write_value, op);
            if (failure != CHEATS_OK || op->kind != OP_WRITE) {
                failure = CHEATS_INVALID_REPEAT;
                goto failed;
            }
            op->repeat = repeat;
            op->stride = (uint8_t)first;
            op->increment = value;
        } else {
            failure = decode(first, value, op);
            if (failure != CHEATS_OK) goto failed;
        }
        failure = validate_address(op, ram_bytes);
        if (failure != CHEATS_OK) goto failed;
        ++program->count;
    }
    for (i = program->count; i-- > 0;) {
        Operation *op = &program->operations[i];
        if (op->kind != OP_WRITE) {
            if (i + 1 == program->count) {
                line = op->source_line;
                failure = CHEATS_ORPHAN_CONDITIONAL;
                goto failed;
            }
            op->false_next = program->operations[i + 1].kind == OP_WRITE
                ? i + 2 : program->operations[i + 1].false_next;
        }
    }
    if (error) *error = (CheatsError){CHEATS_OK, 0};
    return program;
failed:
    free(program);
    if (error) *error = (CheatsError){failure, line};
    return NULL;
}

void cheats_free(CheatsProgram *program)
{
    free(program);
}

void cheats_apply(const CheatsProgram *program, const CheatsMemory *memory)
{
    size_t i = 0;
    while (i < program->count) {
        const Operation *op = &program->operations[i];
        if (op->kind == OP_WRITE) {
            unsigned n;
            for (n = 0; n < op->repeat; ++n) {
                uint16_t value = (uint16_t)(op->value + n * op->increment);
                if (op->width == CHEATS_WIDTH_8) value &= 0xffu;
                memory->write(memory->context, op->address + n * op->stride,
                              op->width, value);
            }
            ++i;
        } else {
            uint16_t actual = memory->read(memory->context, op->address, op->width);
            int pass = 0;
            switch (op->kind) {
            case OP_EQUAL: pass = actual == op->value; break;
            case OP_NOT_EQUAL: pass = actual != op->value; break;
            case OP_LESS: pass = actual < op->value; break;
            case OP_GREATER: pass = actual > op->value; break;
            case OP_WRITE: break;
            }
            i = pass ? i + 1 : op->false_next;
        }
    }
}

const char *cheats_error_message(CheatsErrorCode error)
{
    switch (error) {
    case CHEATS_OK: return "No error";
    case CHEATS_INVALID_ARGUMENT: return "Empty codes or invalid RAM size";
    case CHEATS_TOO_MANY_CODES: return "Too many code lines";
    case CHEATS_MALFORMED_CODE: return "Expected eight hex digits and four hex digits";
    case CHEATS_UNSUPPORTED_OPCODE: return "Unsupported GameShark opcode";
    case CHEATS_UNSAFE_ADDRESS: return "Code accesses memory outside main RAM";
    case CHEATS_UNALIGNED_ADDRESS: return "16-bit code requires an even RAM address and stride";
    case CHEATS_INVALID_BYTE_VALUE: return "8-bit code value exceeds 00FF";
    case CHEATS_ORPHAN_CONDITIONAL: return "Conditional has no following write";
    case CHEATS_INVALID_REPEAT: return "Repeat requires a nonzero count and a following 80 or 30 write";
    case CHEATS_OUT_OF_MEMORY: return "Cannot allocate cheat program";
    }
    return "Unknown cheat error";
}
