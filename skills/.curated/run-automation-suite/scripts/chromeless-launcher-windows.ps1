# chromeless-launcher-windows.ps1 — Windows shim invoked by SKILL.md Step 5.
#
# Launches Chrome in --app mode pointing at the device-only URL, then polls
# (up to 30s) for the new window and resizes it via SetWindowPos. Matches
# the new window by a snapshot-before / diff-after over all visible
# top-level Chrome windows: this works whether Chrome was already running
# (in which case `chrome.exe --app=` delegates to the existing instance
# and the spawned PID has no children) or started fresh. Window title is
# unreliable (Chrome --app windows inherit the page title, not the URL).
#
# Exit codes mirror chromeless-launcher.sh:
#   0  — Chrome launched (resize may have failed; logged + tolerated)
#   2  — Chrome not detected; caller should fall through to default browser
#   64 — usage error
#
# Args: -Url <URL> [-Width <N>] [-Height <N>] [-X <N>] [-Y <N>]

param(
  [Parameter(Mandatory = $true)] [string] $Url,
  [int] $Width = 540,
  [int] $Height = 920,
  [int] $X = 100,
  [int] $Y = 100
)

$ErrorActionPreference = 'Continue'

# --- Numeric arg validation -----------------------------------------------
# PowerShell's [int] cast rejects non-numeric strings at param-binding time,
# but a caller can still pass zero or negative dimensions. Reject those
# explicitly so they fail with the documented exit-64 contract rather than
# producing an invalid SetWindowPos call.
foreach ($pair in @(@('-Width', $Width), @('-Height', $Height), @('-X', $X), @('-Y', $Y))) {
  if ($pair[1] -le 0) {
    Write-Error ('chromeless-launcher-windows: {0} must be a positive integer (got: {1})' -f $pair[0], $pair[1])
    exit 64
  }
}

# --- URL validation --------------------------------------------------------
# Only `"` (which would break CreateProcess argument quoting) and
# non-http(s) schemes are rejected. URL syntax characters (`&`, `?`,
# `=`, `;`, `|`, `<`, `>`, single-quote, backtick, `$`, `\`) are valid
# inside a URL value passed to Start-Process as an array element and
# Kobiton portal URLs depend on `&` and `?` between query params.
if ($Url -match '"' -or $Url -notmatch '^https?://') {
  Write-Error 'chromeless-launcher-windows: --url must be a clean http(s) URL with no embedded double quotes'
  exit 64
}

# --- Detect Chrome binary --------------------------------------------------
$chromePaths = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chrome) {
  Write-Error 'chromeless launcher requires Google Chrome or Chromium — falling back to default browser'
  exit 2
}

# --- Win32 P/Invoke shim for SetWindowPos + EnumWindows --------------------
if (-not ('ChromelessWin' -as [type])) {
  Add-Type -TypeDefinition @"
    using System;
    using System.Collections.Generic;
    using System.Runtime.InteropServices;
    using System.Diagnostics;
    public class ChromelessWin {
      public delegate bool EnumProc(IntPtr hwnd, IntPtr lparam);

      [DllImport("user32.dll")]
      public static extern bool EnumWindows(EnumProc proc, IntPtr lParam);

      [DllImport("user32.dll")]
      public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);

      [DllImport("user32.dll")]
      public static extern bool IsWindowVisible(IntPtr hwnd);

      [DllImport("user32.dll")]
      public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y,
                                             int cx, int cy, uint flags);

      // Snapshot all current top-level visible HWNDs owned by chrome.exe processes.
      public static HashSet<IntPtr> SnapshotChromeWindows() {
        var snap = new HashSet<IntPtr>();
        var chromeNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "chrome.exe", "chromium.exe" };
        var chromePids = new HashSet<uint>();
        foreach (var p in Process.GetProcesses()) {
          try { if (chromeNames.Contains(p.ProcessName + ".exe")) chromePids.Add((uint)p.Id); } catch {}
        }
        EnumProc cb = delegate(IntPtr hwnd, IntPtr lp) {
          if (!IsWindowVisible(hwnd)) return true;
          uint pid;
          GetWindowThreadProcessId(hwnd, out pid);
          if (chromePids.Contains(pid)) snap.Add(hwnd);
          return true;
        };
        EnumWindows(cb, IntPtr.Zero);
        return snap;
      }

      // Find a new top-level visible HWND owned by any chrome.exe process
      // that was not present in the pre-launch snapshot.
      public static IntPtr FindNewChromeWindow(HashSet<IntPtr> snapshot) {
        var chromeNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "chrome.exe", "chromium.exe" };
        var chromePids = new HashSet<uint>();
        foreach (var p in Process.GetProcesses()) {
          try { if (chromeNames.Contains(p.ProcessName + ".exe")) chromePids.Add((uint)p.Id); } catch {}
        }
        IntPtr found = IntPtr.Zero;
        EnumProc cb = delegate(IntPtr hwnd, IntPtr lp) {
          if (!IsWindowVisible(hwnd)) return true;
          if (snapshot.Contains(hwnd)) return true;
          uint pid;
          GetWindowThreadProcessId(hwnd, out pid);
          if (chromePids.Contains(pid)) { found = hwnd; return false; }
          return true;
        };
        EnumWindows(cb, IntPtr.Zero);
        return found;
      }
    }
"@
}

# --- Snapshot existing Chrome windows before launch ------------------------
$snapshot = [ChromelessWin]::SnapshotChromeWindows()

# --- Spawn Chrome --app ----------------------------------------------------
# Pass --app as a single array element so PowerShell's argument-list
# handling quotes the value as one token rather than splitting on spaces.
# URL validation above guarantees the value contains no embedded double quotes.
# If Chrome is already running it will delegate to the existing instance and
# exit immediately — that's fine; we detect the new window by snapshot diff.
Start-Process -FilePath $chrome -ArgumentList @("--app=$Url") -WindowStyle Normal

# --- Poll for the new window, then resize ----------------------------------
$deadline = (Get-Date).AddSeconds(30)
$hwnd = [IntPtr]::Zero

while ((Get-Date) -lt $deadline -and $hwnd -eq [IntPtr]::Zero) {
  $hwnd = [ChromelessWin]::FindNewChromeWindow($snapshot)
  if ($hwnd -eq [IntPtr]::Zero) { Start-Sleep -Seconds 1 }
}

if ($hwnd -ne [IntPtr]::Zero) {
  # SWP_NOZORDER (0x0004) | SWP_NOACTIVATE (0x0010) = 0x0014
  [ChromelessWin]::SetWindowPos($hwnd, [IntPtr]::Zero, $X, $Y, $Width, $Height, 0x0014) | Out-Null
  exit 0
}

Write-Error 'chromeless-launcher-windows: window did not appear within 30s; user can resize manually'
exit 0
