# Copy each starter cheat list next to the executable only when none is there
# yet. The copy beside the game is the player's list: the launcher edits it,
# so a rebuild must never overwrite it.
file(GLOB _lists "${SRC}/*.toml")
foreach(_list IN LISTS _lists)
    get_filename_component(_name "${_list}" NAME)
    if(NOT EXISTS "${DST}/${_name}")
        file(COPY "${_list}" DESTINATION "${DST}")
    endif()
endforeach()
