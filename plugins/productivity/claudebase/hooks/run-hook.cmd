: ; # Polyglot wrapper — cmd.exe runs the batch block, Unix shells run the bash block
: ; # On Windows: finds Git Bash and delegates. On Unix: runs directly.
: ;
: ; SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)/scripts"
: ; HOOK_SCRIPT="${1:-}"
: ; if [ -z "$HOOK_SCRIPT" ]; then echo "[claudebase] Error: No script argument provided." >&2; exit 1; fi
: ; if [ ! -f "${SCRIPT_DIR}/${HOOK_SCRIPT}" ]; then echo "[claudebase] Error: Script not found: ${SCRIPT_DIR}/${HOOK_SCRIPT}" >&2; exit 1; fi
: ; shift
: ; exec bash "${SCRIPT_DIR}/${HOOK_SCRIPT}" "$@"
: ; exit

@echo off
setlocal

:: Find Git Bash on Windows
set "GIT_BASH="
where git >nul 2>&1 && (
    for /f "delims=" %%i in ('where git') do (
        set "GIT_DIR=%%~dpi"
    )
)
if defined GIT_DIR (
    set "GIT_BASH=%GIT_DIR%..\bin\bash.exe"
)

if not exist "%GIT_BASH%" (
    if exist "C:\Program Files\Git\bin\bash.exe" (
        set "GIT_BASH=C:\Program Files\Git\bin\bash.exe"
    ) else if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
        set "GIT_BASH=C:\Program Files (x86)\Git\bin\bash.exe"
    ) else (
        echo [claudebase] Error: Git Bash not found. Install Git for Windows. >&2
        exit /b 1
    )
)

"%GIT_BASH%" "%~f0" %*
exit /b %errorlevel%
