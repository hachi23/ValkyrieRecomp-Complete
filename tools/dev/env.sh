#!/bin/bash
# Shared env for building ValkyrieRecomp under MSYS2 MinGW64
export MSYSTEM=MINGW64
export PATH="/mingw64/bin:/usr/bin:/c/VulkanSDK/1.4.363.0/Bin:$PATH"
export VULKAN_SDK="C:/VulkanSDK/1.4.363.0"
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
