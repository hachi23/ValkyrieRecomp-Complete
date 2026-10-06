include_guard(GLOBAL)

include(FetchContent)
include("${CMAKE_CURRENT_LIST_DIR}/../cmake/psx_dependency_archive.cmake")

# RetroAchievements (rcheevos, MIT). Optional: built only when libcurl is
# available for its HTTPS requests. The pinned archive is vendored under
# third_party/ like libchdr so offline builds do not need github.com.
option(PSX_ENABLE_RCHEEVOS "Build RetroAchievements support (needs libcurl)" ON)
set(PSX_HAVE_RCHEEVOS OFF)
if(PSX_ENABLE_RCHEEVOS)
    find_package(CURL QUIET)
endif()
if(PSX_ENABLE_RCHEEVOS AND CURL_FOUND)
    psxrecomp_dependency_source_dir(psx_rcheevos
        ENV PSX_RCHEEVOS_SOURCE_DIR
        OUT _psx_rcheevos_src)
    psxrecomp_dependency_archive(psx_rcheevos
        SOURCE_DIR "${_psx_rcheevos_src}"
        OUT_URL _psx_rcheevos_url OUT_HASH _psx_rcheevos_hash)
    FetchContent_Declare(psx_rcheevos
        URL "${_psx_rcheevos_url}"
        URL_HASH "${_psx_rcheevos_hash}")
    FetchContent_MakeAvailable(psx_rcheevos)
    file(GLOB _psx_rc_sources
        "${psx_rcheevos_SOURCE_DIR}/src/*.c"
        "${psx_rcheevos_SOURCE_DIR}/src/rapi/*.c"
        "${psx_rcheevos_SOURCE_DIR}/src/rcheevos/*.c"
        "${psx_rcheevos_SOURCE_DIR}/src/rhash/*.c")
    # rc_libretro.c adapts libretro cores and needs libretro.h; not ours.
    list(FILTER _psx_rc_sources EXCLUDE REGEX "rc_libretro\\.c$")
    add_library(psx_rcheevos STATIC ${_psx_rc_sources})
    target_include_directories(psx_rcheevos PUBLIC "${psx_rcheevos_SOURCE_DIR}/include"
        PRIVATE "${psx_rcheevos_SOURCE_DIR}/src")
    target_compile_definitions(psx_rcheevos PUBLIC RC_CLIENT_SUPPORTS_HASH=1)
    set_target_properties(psx_rcheevos PROPERTIES POSITION_INDEPENDENT_CODE ON)
    set(PSX_HAVE_RCHEEVOS ON)
    message(STATUS "psxrecomp: RetroAchievements enabled (rcheevos 12.5.0, libcurl ${CURL_VERSION_STRING})")
elseif(PSX_ENABLE_RCHEEVOS)
    message(STATUS "psxrecomp: RetroAchievements disabled (libcurl not found)")
endif()
