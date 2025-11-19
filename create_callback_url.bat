@echo off
REM This batch will create a LinkedIn OAuth authorization URL using variables from .env.yaml
REM The resulting URL will be printed to the console.
REM You may copy and paste it into your browser to test the OAuth flow.
REM The URL must be shared with the client that will authorize our Linkedin app to access the Linkedin API on their behalf.

REM ======================
REM  Step 1: Convert .env.yaml to .tmp_env
REM ======================
echo Converting .env.yaml to .tmp_env ...
del .env 2>nul

for /f "usebackq tokens=1,* delims=:" %%a in (".env.yaml") do (
    if /i not "%%a"=="env_variables" (
        set "key=%%a"
        set "value=%%b"
        setlocal enabledelayedexpansion
        rem Remove leading/trailing spaces from key
        set "key=!key: =!"
        rem Trim leading spaces from value and remove quotes
        for /f "tokens=* delims= " %%v in ("!value!") do set "value=%%v"
        set "value=!value:\"=!"
        echo !key!=!value!>> .tmp_env
        endlocal
    )
)

REM ======================
REM  Step 2: Load variables from .tmp_env
REM ======================
setlocal enabledelayedexpansion
for /f "tokens=1,* delims==" %%a in (.tmp_env) do (
    if "%%a"=="LINKEDIN_CLIENT_ID" set CLIENT_ID=%%b
    if "%%a"=="REDIRECT_URI" set REDIRECT_URI=%%b
    if "%%a"=="STATE" set STATE=%%b
    if "%%a"=="SCOPE" set SCOPE=%%b
)

REM ======================
REM  Step 3: Clean quotes from variables
REM ======================
set "CLIENT_ID=!CLIENT_ID:"=!"
set "REDIRECT_URI=!REDIRECT_URI:"=!"
set "STATE=!STATE:"=!"
set "SCOPE=!SCOPE:"=!"

REM Encode spaces in SCOPE to %20
set "SCOPE=!SCOPE: =%%20!"

REM ======================
REM  Step 4: Output final LinkedIn OAuth URL
REM ======================
echo.
echo LinkedIn OAuth URL:
echo https://www.linkedin.com/oauth/v2/authorization^
?response_type=code^
&client_id=!CLIENT_ID!^
&redirect_uri=!REDIRECT_URI!^
&scope=!SCOPE!^
&state=!STATE!
echo.

del .tmp_env 2>nul
pause
