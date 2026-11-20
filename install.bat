@echo off
setlocal EnableDelayedExpansion

echo =======================================================
echo    Installation - VLC Music Controller (Apple Style)
echo =======================================================
echo.

REM 1. Verification de VLC
set "VLC_PATH1=C:\Program Files\VideoLAN\VLC\vlc.exe"
set "VLC_PATH2=C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
set "VLC_FOUND=0"

if exist "%VLC_PATH1%" set "VLC_FOUND=1"
if exist "%VLC_PATH2%" set "VLC_FOUND=1"
where vlc >nul 2>&1
if !errorlevel! equ 0 set "VLC_FOUND=1"

if "!VLC_FOUND!"=="1" (
    echo [OK] VLC Media Player est present.
) else (
    echo [i] VLC non detecte. Installation automatique via winget...
    winget install VideoLAN.VLC --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] VLC installe avec succes.
    ) else (
        echo [!] Impossible d'installer VLC automatiquement.
    )
)

echo.
REM 2. Preparation de l'application autonome
set "TARGET_EXE=%~dp0VLC_Ctrl.exe"
set "ICON_PATH=%~dp0app_icon.ico"

if exist "%TARGET_EXE%" (
    echo [OK] Executable autonome VLC_Ctrl.exe pret.
) else (
    echo [i] Compilation de VLC_Ctrl.exe via PyInstaller...
    python -m pip install --quiet --disable-pip-version-check -r "%~dp0Requirements.txt"
    pyinstaller --noconsole --onefile --clean --icon="app_icon.ico" --name="VLC_Ctrl" --distpath="." --collect-all customtkinter "Vlcctrl.pyw" >nul 2>&1
    if exist "%TARGET_EXE%" (
        echo [OK] VLC_Ctrl.exe compile avec succes.
    ) else (
        set "TARGET_EXE=pythonw.exe"
        set "TARGET_ARGS=""%~dp0Vlcctrl.pyw"""
    )
)

echo.
REM 3. Proposition d'ajout au Menu Demarrer (avec timeout automatique de 5s)
choice /c ON /t 5 /d O /m "Ajouter un raccourci dans le Menu Demarrer (defaut: O) ?"
if !errorlevel! equ 1 (
    set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
    set "VBS1=%TEMP%\create_startmenu_lnk.vbs"
    echo Set oWS = WScript.CreateObject("WScript.Shell") > "!VBS1!"
    echo sLink = "!STARTMENU_DIR!\VLC Controller.lnk" >> "!VBS1!"
    echo Set oLink = oWS.CreateShortcut(sLink) >> "!VBS1!"
    echo oLink.TargetPath = "%TARGET_EXE%" >> "!VBS1!"
    if defined TARGET_ARGS echo oLink.Arguments = "%TARGET_ARGS%" >> "!VBS1!"
    echo oLink.WorkingDirectory = "%~dp0" >> "!VBS1!"
    echo oLink.Description = "Controleur VLC Apple Style" >> "!VBS1!"
    if exist "%ICON_PATH%" echo oLink.IconLocation = "%ICON_PATH%,0" >> "!VBS1!"
    echo oLink.Save >> "!VBS1!"
    cscript //nologo "!VBS1!" >nul 2>&1
    if exist "!VBS1!" del /f /q "!VBS1!" >nul 2>&1
    echo [OK] Raccourci ajoute au Menu Demarrer de Windows.
) else (
    echo [i] Raccourci Menu Demarrer ignore.
)

echo.
REM 4. Proposition d'ajout au Demarrage de Windows (Startup)
choice /c ON /t 5 /d O /m "Lancer automatiquement au demarrage de Windows (defaut: O) ?"
if !errorlevel! equ 1 (
    set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    set "VBS2=%TEMP%\create_startup_lnk.vbs"
    echo Set oWS = WScript.CreateObject("WScript.Shell") > "!VBS2!"
    echo sLink = "!STARTUP_DIR!\VLC Controller.lnk" >> "!VBS2!"
    echo Set oLink = oWS.CreateShortcut(sLink) >> "!VBS2!"
    echo oLink.TargetPath = "%TARGET_EXE%" >> "!VBS2!"
    if defined TARGET_ARGS echo oLink.Arguments = "%TARGET_ARGS%" >> "!VBS2!"
    echo oLink.WorkingDirectory = "%~dp0" >> "!VBS2!"
    echo oLink.Description = "Controleur VLC Apple Style" >> "!VBS2!"
    if exist "%ICON_PATH%" echo oLink.IconLocation = "%ICON_PATH%,0" >> "!VBS2!"
    echo oLink.Save >> "!VBS2!"
    cscript //nologo "!VBS2!" >nul 2>&1
    if exist "!VBS2!" del /f /q "!VBS2!" >nul 2>&1
    echo [OK] Raccourci de demarrage automatique cree.
) else (
    echo [i] Lancement au demarrage ignore.
)

echo.
REM 5. Lancement de l'application
echo [i] Lancement du controleur VLC...
start "" "%TARGET_EXE%" %TARGET_ARGS%

echo.
echo =======================================================
echo [SUCCES] Installation terminee !
echo Le controleur VLC est pret et actif.
echo =======================================================
ping 127.0.0.1 -n 3 >nul 2>&1
exit /b 0
