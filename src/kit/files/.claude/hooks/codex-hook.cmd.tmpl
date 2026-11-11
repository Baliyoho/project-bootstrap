@echo off
rem source: PROJECT-BOOTSTRAP.md v2026-11-01.4 - authority is the kit; edit it first, then sync.
rem Codex Windows launcher. Plumbing only; rules stay in the existing .sh files.
rem ASCII-only, LF-only, no labels or multiline parenthesised blocks. See section 3.17.
setlocal
if "%~1"=="" >&2 echo [codex-hook] ERROR: missing script argument.
if "%~1"=="" exit /b 1
set "BASH="
for /f "delims=" %%G in ('where git 2^>nul') do if not defined BASH if exist "%%~dpG..\bin\bash.exe" set "BASH=%%~dpG..\bin\bash.exe"
if not defined BASH if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "BASH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not defined BASH >&2 echo [codex-hook] ERROR: Git Bash not found; hook did not run. Install Git for Windows and retry.
if not defined BASH exit /b 1
rem Codex 0.166.0 treats stdout starting with [ as JSON. Keep a plain-text first line.
echo Git status check:
"%BASH%" "%~dp0%~1"
exit /b %ERRORLEVEL%
