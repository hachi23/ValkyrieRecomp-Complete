param([string[]]$Keys, [string]$Proc = "ValkyrieRecomp", [int]$GapMs = 150)
# Post key presses to the game window only (no global input injection).
# Keys: F5, F6, Up, Down, Return, Escape, Shift+F6 ...
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class KP {
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern uint MapVirtualKey(uint code, uint type);
}
"@
$VK = @{ Up=0x26; Down=0x28; Left=0x25; Right=0x27; Return=0x0D; Escape=0x1B; Shift=0x10; Space=0x20 }
foreach ($n in 1..12) { $VK["F$n"] = 0x6F + $n }
$EXT = @('Up','Down','Left','Right')
$h = (Get-Process $Proc | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1).MainWindowHandle
function Send($name, $down) {
  $vk = $VK[$name]; $sc = [KP]::MapVirtualKey($vk, 0)
  $l = 1 -bor ($sc -shl 16)
  if ($EXT -contains $name) { $l = $l -bor (1 -shl 24) }
  if (-not $down) { $l = $l -bor (3 -shl 30) }
  [void][KP]::PostMessage($h, $(if ($down) {0x100} else {0x101}), [IntPtr]$vk, [IntPtr]$l)
}
foreach ($k in $Keys) {
  $parts = $k -split '\+'
  foreach ($p in $parts) { Send $p $true; Start-Sleep -Milliseconds 30 }
  [array]::Reverse($parts)
  foreach ($p in $parts) { Send $p $false; Start-Sleep -Milliseconds 30 }
  Start-Sleep -Milliseconds $GapMs
}
