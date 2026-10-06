#!/bin/sh
# Starts Valkyrie Profile from this folder so the discs and saves next to it are found.
cd "$(dirname "$0")" && exec ./ValkyrieRecomp "$@"
