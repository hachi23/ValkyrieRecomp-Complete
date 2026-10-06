param([string]$Out, [string]$Proc = "ValkyrieRecomp")
# Capture ONLY the game window (PrintWindow, works even when covered) to a PNG.
# Never screen-scrapes the desktop.
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WinCap {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@
[void][WinCap]::SetProcessDPIAware()
$p = Get-Process $Proc -ErrorAction Stop | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
$h = $p.MainWindowHandle
$r = New-Object WinCap+RECT; [void][WinCap]::GetClientRect($h, [ref]$r)
$w = $r.R - $r.L; $ht = $r.B - $r.T
$bmp = New-Object System.Drawing.Bitmap $w, $ht
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
# 1 = PW_CLIENTONLY, 2 = PW_RENDERFULLCONTENT (needed for GPU-presented windows)
$ok = [WinCap]::PrintWindow($h, $hdc, 3)
$g.ReleaseHdc($hdc)
if (-not $ok) { throw "PrintWindow failed" }
$scale = [Math]::Min(1.0, 960.0 / $w)
$sw = [int]($w * $scale); $sh = [int]($ht * $scale)
$small = New-Object System.Drawing.Bitmap $sw, $sh
$g2 = [System.Drawing.Graphics]::FromImage($small)
$g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBilinear
$g2.DrawImage($bmp, 0, 0, $sw, $sh)
$small.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
"captured ${w}x${ht} -> ${sw}x${sh}"
