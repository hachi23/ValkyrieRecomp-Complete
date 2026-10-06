#ifndef PSX_CHEATS_H
#define PSX_CHEATS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct CheatsProgram CheatsProgram;

typedef enum CheatsWidth {
    CHEATS_WIDTH_8 = 1,
    CHEATS_WIDTH_16 = 2
} CheatsWidth;

typedef struct CheatsMemory {
    void *context;
    uint16_t (*read)(void *context, uint32_t ram_offset, CheatsWidth width);
    void (*write)(void *context, uint32_t ram_offset, CheatsWidth width,
                  uint16_t value);
} CheatsMemory;

typedef enum CheatsErrorCode {
    CHEATS_OK,
    CHEATS_INVALID_ARGUMENT,
    CHEATS_TOO_MANY_CODES,
    CHEATS_MALFORMED_CODE,
    CHEATS_UNSUPPORTED_OPCODE,
    CHEATS_UNSAFE_ADDRESS,
    CHEATS_UNALIGNED_ADDRESS,
    CHEATS_INVALID_BYTE_VALUE,
    CHEATS_ORPHAN_CONDITIONAL,
    CHEATS_INVALID_REPEAT,
    CHEATS_OUT_OF_MEMORY
} CheatsErrorCode;

typedef struct CheatsError {
    CheatsErrorCode code;
    size_t line;
} CheatsError;

CheatsProgram *cheats_compile(const char *const *codes, size_t count,
                             uint32_t ram_bytes, CheatsError *error);
void cheats_free(CheatsProgram *program);
void cheats_apply(const CheatsProgram *program, const CheatsMemory *memory);
const char *cheats_error_message(CheatsErrorCode error);

#ifdef __cplusplus
}
#endif
#endif
