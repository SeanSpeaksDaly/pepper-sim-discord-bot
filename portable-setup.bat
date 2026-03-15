@echo off
REM ============================================================================
REM  PORTABLE DISCORD BOT HOST SETUP
REM  Drop this on a USB, plug into any Windows PC, and run it.
REM  It installs everything from scratch and gets your bots running.
REM ============================================================================

title Discord Bot Host - Portable Setup
color 0A
echo.
echo  =============================================
echo   DISCORD BOT HOST - PORTABLE INSTALLER
echo   Plug in. Run. Farm peppers.
echo  =============================================
echo.
echo  This script will install:
echo    - Python 3
echo    - Node.js
echo    - PM2 (process manager)
echo    - pip packages
echo    - Your bot(s)
echo.
echo  Press any key to start, or close this window to cancel.
pause >nul

REM ============================================================================
REM  STEP 1 - PYTHON
REM ============================================================================
echo.
echo  [1/7] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  FOUND - Python already installed.
    goto :python_done
)
echo  Python not found. Installing...
winget install Python.Python.3.13 --accept-package-agreements --accept-source-agreements >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  Python installed via winget.
    goto :python_done
)
echo.
echo  !! Could not auto-install Python.
echo  !! Download it manually: https://www.python.org/downloads/
echo  !! IMPORTANT: Check "Add Python to PATH" during install.
echo  !! Then re-run this script.
pause
exit /b 1
:python_done

REM ============================================================================
REM  STEP 2 - NODE.JS
REM ============================================================================
echo.
echo  [2/7] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  FOUND - Node.js already installed.
    goto :node_done
)
echo  Node.js not found. Installing...
winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  Node.js installed via winget.
    echo.
    echo  !! YOU NEED TO RESTART THIS SCRIPT !!
    echo  !! Close this window, open a new terminal, and run this again.
    pause
    exit /b 0
)
echo.
echo  !! Could not auto-install Node.js.
echo  !! Download it manually: https://nodejs.org/
echo  !! Then re-run this script.
pause
exit /b 1
:node_done

REM ============================================================================
REM  STEP 3 - GIT
REM ============================================================================
echo.
echo  [3/7] Checking Git...
git --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  FOUND - Git already installed.
    goto :git_done
)
echo  Git not found. Installing...
winget install Git.Git --accept-package-agreements --accept-source-agreements >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  Git installed via winget.
    echo.
    echo  !! YOU NEED TO RESTART THIS SCRIPT !!
    echo  !! Close this window, open a new terminal, and run this again.
    pause
    exit /b 0
)
echo.
echo  !! Could not auto-install Git.
echo  !! Download it manually: https://git-scm.com/downloads
echo  !! Then re-run this script.
pause
exit /b 1
:git_done

REM ============================================================================
REM  STEP 4 - PM2
REM ============================================================================
echo.
echo  [4/7] Installing PM2 process manager...
call npm list -g pm2 >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  FOUND - PM2 already installed.
) else (
    call npm install -g pm2 >nul 2>&1
    echo  PM2 installed.
)

REM ============================================================================
REM  STEP 5 - DIRECTORY STRUCTURE
REM ============================================================================
echo.
echo  [5/7] Creating bot directory...
set "BOTS_HOME=%USERPROFILE%\discord-bots"
if not exist "%BOTS_HOME%" mkdir "%BOTS_HOME%"
if not exist "%BOTS_HOME%\logs" mkdir "%BOTS_HOME%\logs"
echo  Created: %BOTS_HOME%

REM ============================================================================
REM  STEP 6 - BOT MANAGER CLI
REM ============================================================================
echo.
echo  [6/7] Creating bot manager...

(
echo @echo off
echo setlocal enabledelayedexpansion
echo set "BOTS_HOME=%%USERPROFILE%%\discord-bots"
echo set "CMD=%%~1"
echo set "BOT=%%~2"
echo set "ARG3=%%~3"
echo.
echo if "%%CMD%%"=="" goto :usage
echo if "%%CMD%%"=="list" goto :list
echo if "%%CMD%%"=="logs" goto :logs
echo if "%%CMD%%"=="monit" goto :monit
echo if "%%CMD%%"=="save" goto :save
echo if "%%BOT%%"=="" goto :usage
echo if "%%CMD%%"=="add" goto :add
echo if "%%CMD%%"=="clone" goto :clone
echo if "%%CMD%%"=="start" goto :start
echo if "%%CMD%%"=="stop" goto :stop
echo if "%%CMD%%"=="restart" goto :restart
echo if "%%CMD%%"=="update" goto :update
echo if "%%CMD%%"=="remove" goto :remove
echo if "%%CMD%%"=="token" goto :token
echo goto :usage
echo.
echo :clone
echo if "%%ARG3%%"=="" ^(
echo     echo Usage: bot clone ^<name^> ^<github-url^>
echo     goto :eof
echo ^)
echo echo Cloning %%ARG3%% into %%BOTS_HOME%%\%%BOT%%...
echo git clone "%%ARG3%%" "%%BOTS_HOME%%\%%BOT%%"
echo echo.
echo echo Done! Now run:
echo echo   bot token %%BOT%%    ^(set your discord token^)
echo echo   bot add %%BOT%%      ^(start the bot^)
echo goto :eof
echo.
echo :token
echo set /p "TKN=Enter Discord token for %%BOT%%: "
echo echo DISCORD_TOKEN=%%TKN%%^> "%%BOTS_HOME%%\%%BOT%%\.env"
echo echo Token saved to %%BOTS_HOME%%\%%BOT%%\.env
echo goto :eof
echo.
echo :add
echo if "%%ARG3%%"=="" ^( set "ENTRY=bot.py" ^) else ^( set "ENTRY=%%ARG3%%" ^)
echo echo Adding bot: %%BOT%% ^(%%ENTRY%%^)
echo cd /d "%%BOTS_HOME%%\%%BOT%%"
echo if exist requirements.txt pip install -r requirements.txt --quiet
echo call pm2 start "%%ENTRY%%" --name "%%BOT%%" --interpreter python --cwd "%%BOTS_HOME%%\%%BOT%%" --log "%%BOTS_HOME%%\logs\%%BOT%%.log" --restart-delay 5000 --max-restarts 10
echo call pm2 save
echo echo %%BOT%% is now running!
echo goto :eof
echo.
echo :start
echo call pm2 start "%%BOT%%"
echo goto :eof
echo.
echo :stop
echo call pm2 stop "%%BOT%%"
echo goto :eof
echo.
echo :restart
echo call pm2 restart "%%BOT%%"
echo goto :eof
echo.
echo :update
echo echo Updating %%BOT%%...
echo cd /d "%%BOTS_HOME%%\%%BOT%%"
echo git pull
echo if exist requirements.txt pip install -r requirements.txt --quiet
echo call pm2 restart "%%BOT%%"
echo echo %%BOT%% updated and restarted.
echo goto :eof
echo.
echo :remove
echo call pm2 delete "%%BOT%%"
echo call pm2 save
echo echo %%BOT%% removed.
echo goto :eof
echo.
echo :list
echo call pm2 list
echo goto :eof
echo.
echo :logs
echo if "%%BOT%%"=="" ^( call pm2 logs --lines 50 ^) else ^( call pm2 logs "%%BOT%%" --lines 50 ^)
echo goto :eof
echo.
echo :monit
echo call pm2 monit
echo goto :eof
echo.
echo :save
echo call pm2 save
echo echo Bot list saved. They will restart on reboot.
echo goto :eof
echo.
echo :usage
echo.
echo   ==========================================
echo    Discord Bot Manager
echo   ==========================================
echo.
echo   SETUP:
echo     bot clone ^<name^> ^<github-url^>   Clone a bot repo
echo     bot token ^<name^>                Set the Discord token
echo     bot add ^<name^> [entry.py]       Register and start
echo.
echo   CONTROL:
echo     bot start ^<name^>      Start a stopped bot
echo     bot stop ^<name^>       Stop a running bot
echo     bot restart ^<name^>    Restart a bot
echo     bot update ^<name^>     Git pull + restart
echo     bot remove ^<name^>     Remove from PM2
echo.
echo   INFO:
echo     bot list              All bots + status
echo     bot logs [name]       View logs
echo     bot monit             Live dashboard
echo     bot save              Save for reboot
echo.
echo   EXAMPLE:
echo     bot clone spice https://github.com/YOU/repo.git
echo     bot token spice
echo     bot add spice bot.py
echo.
echo   Bots folder: %%BOTS_HOME%%
echo.
echo goto :eof
) > "%BOTS_HOME%\bot.bat"

echo  Created: %BOTS_HOME%\bot.bat

REM ============================================================================
REM  STEP 7 - ADD TO PATH
REM ============================================================================
echo.
echo  [7/7] Adding bot command to PATH...

REM Check if already in PATH
echo %PATH% | findstr /i "discord-bots" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  Already in PATH.
) else (
    setx PATH "%PATH%;%BOTS_HOME%" >nul 2>&1
    set "PATH=%PATH%;%BOTS_HOME%"
    echo  Added to PATH.
)

REM ============================================================================
REM  DONE
REM ============================================================================
echo.
echo  =============================================
echo   SETUP COMPLETE!
echo  =============================================
echo.
echo  CLOSE THIS WINDOW and open a new terminal.
echo.
echo  Then to get your first bot running:
echo.
echo    bot clone spice-and-dice https://github.com/SeanSpeaksDaly/pepper-sim-discord-bot.git
echo    bot token spice-and-dice
echo    bot add spice-and-dice bot.py
echo.
echo  That's it! Three commands and you're farming.
echo.
echo  =============================================
echo.
pause
