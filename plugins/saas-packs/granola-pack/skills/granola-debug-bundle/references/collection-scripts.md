# Granola Debug Bundle Collection Scripts

## macOS System Information

```bash
# Create debug directory
mkdir -p ~/Desktop/granola-debug
cd ~/Desktop/granola-debug

# System info
sw_vers > system-info.txt
system_profiler SPHardwareDataType >> system-info.txt
system_profiler SPSoftwareDataType >> system-info.txt

# Audio configuration
system_profiler SPAudioDataType > audio-config.txt

# Display info
system_profiler SPDisplaysDataType > display-info.txt
```

## Windows System Information

```powershell
mkdir $env:USERPROFILE\Desktop\granola-debug
cd $env:USERPROFILE\Desktop\granola-debug

systeminfo > system-info.txt
Get-WmiObject Win32_SoundDevice | Out-File audio-devices.txt
```

## Granola Logs Collection

### macOS

```bash
# Granola application logs
cp -r ~/Library/Logs/Granola ./granola-logs 2>/dev/null

# Application support data (no sensitive data)
ls -la ~/Library/Application\ Support/Granola/ > app-support-listing.txt

# System logs related to Granola
log show --predicate 'process == "Granola"' --last 1h > system-logs.txt 2>/dev/null
```

### Windows

```powershell
Copy-Item "$env:LOCALAPPDATA\Granola\logs" -Destination ".\granola-logs" -Recurse
Get-EventLog -LogName Application -Source "Granola" -Newest 100 | Out-File app-events.txt
```

## Network Diagnostics

```bash
set -euo pipefail
curl -s -o /dev/null -w "%{http_code}" https://api.granola.ai/health > network-test.txt
curl -s -o /dev/null -w "%{http_code}" https://granola.ai >> network-test.txt
nslookup api.granola.ai >> network-test.txt 2>&1
traceroute -m 10 api.granola.ai >> network-test.txt 2>&1
```

## Calendar Integration Status Template

```
Calendar Integration Checklist:

1. Calendar Provider: [Google/Outlook/Other]
2. Last Successful Sync: [Date/Time]
3. Connected Calendars: [List]
4. OAuth Token Status: [Valid/Expired/Unknown]
5. Permissions Granted: [Yes/No/Partial]

Recent Calendar Errors:
[Copy any errors from Granola settings]
```

## Audio Configuration Check Template

```
Audio Configuration Report
==========================

Default Input Device: [check system_profiler SPAudioDataType]

Audio Permissions:
- Granola has microphone access: [Yes/No]
- Other apps using microphone: [List]

Virtual Audio Software:
- Loopback: [Installed/Not Installed]
- BlackHole: [Installed/Not Installed]
```

## Package and Submit

```bash
cd ~/Desktop
zip -r granola-debug-$(date +%Y%m%d-%H%M%S).zip granola-debug/
echo "Send this file to help@granola.ai"
```

## Debug Bundle Contents

| File | Purpose |
|------|---------|
| system-info.txt | OS and hardware details |
| audio-config.txt | Audio device configuration |
| granola-logs/ | Application log files |
| network-test.txt | Connectivity diagnostics |
| calendar-status.txt | Calendar integration state |
| audio-check.txt | Microphone configuration |
