@echo off
REM ============================================================================
REM  Discord Bot Host Setup - Windows
REM  Sets up PM2 process manager for running multiple Discord bots
REM ============================================================================

echo.
echo  ============================================
echo   Discord Bot Hosting Environment Setup
echo  ============================================
echo.

REM --- Step 1: Check Python ---
echo [1/5] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  ERROR: Python not found. Install from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
echo  OK - Python found.

REM --- Step 2: Check/Install Node.js ---
echo.
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  Node.js not found. Installing via winget...
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% neq 0 (
        echo  ERROR: Could not install Node.js automatically.
        echo  Install manually from https://nodejs.org/
        pause
        exit /b 1
    )
    echo  Restart this script after Node.js install completes.
    pause
    exit /b 0
)
echo  OK - Node.js found.

REM --- Step 3: Install PM2 ---
echo.
echo [3/5] Installing PM2 process manager...
call npm list -g pm2 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call npm install -g pm2 pm2-windows-startup
    echo  PM2 installed globally.
) else (
    echo  OK - PM2 already installed.
)

REM --- Step 4: Create bot hosting directory structure ---
echo.
echo [4/5] Setting up bot directory structure...

set "BOTS_HOME=%USERPROFILE%\discord-bots"
if not exist "%BOTS_HOME%" mkdir "%BOTS_HOME%"
if not exist "%BOTS_HOME%\logs" mkdir "%BOTS_HOME%\logs"

REM Create the bot manager script
echo  Created %BOTS_HOME%

REM --- Step 5: Manual configuration ---
echo.
echo  ============================================
echo [5/5] MANUAL CONFIGURATION
echo  ============================================
echo.
echo  Your bots directory: %BOTS_HOME%
echo.
echo  To add a bot:
echo    1. Clone your repo into %BOTS_HOME%\
echo       git clone https://github.com/YOU/REPO.git %BOTS_HOME%\my-bot
echo.
echo    2. Create a .env file in that bot folder with your token:
echo       echo DISCORD_TOKEN=your-token-here ^> %BOTS_HOME%\my-bot\.env
echo.
echo    3. Install dependencies:
echo       cd %BOTS_HOME%\my-bot ^&^& pip install -r requirements.txt
echo.
echo    4. Register the bot with PM2:
echo       bot add my-bot bot.py
echo.
echo  ============================================
echo.

REM --- Create the bot manager CLI ---
echo Creating bot manager CLI...

(
echo @echo off
echo REM Bot Manager CLI - manages multiple Discord bots via PM2
echo.
echo set "BOTS_HOME=%%USERPROFILE%%\discord-bots"
echo set "CMD=%%~1"
echo set "BOT=%%~2"
echo set "ENTRY=%%~3"
echo.
echo if "%%CMD%%"=="" goto :usage
echo if "%%CMD%%"=="list" goto :list
echo if "%%CMD%%"=="logs" goto :logs
echo if "%%CMD%%"=="monit" goto :monit
echo if "%%BOT%%"=="" goto :usage
echo if "%%CMD%%"=="add" goto :add
echo if "%%CMD%%"=="start" goto :start
echo if "%%CMD%%"=="stop" goto :stop
echo if "%%CMD%%"=="restart" goto :restart
echo if "%%CMD%%"=="update" goto :update
echo if "%%CMD%%"=="remove" goto :remove
echo goto :usage
echo.
echo :add
echo if "%%ENTRY%%"=="" set "ENTRY=bot.py"
echo echo Adding bot: %%BOT%% ^(%%ENTRY%%^)
echo cd "%%BOTS_HOME%%\%%BOT%%"
echo pip install -r requirements.txt 2^>nul
echo call pm2 start %%ENTRY%% --name %%BOT%% --interpreter python --cwd "%%BOTS_HOME%%\%%BOT%%" --log "%%BOTS_HOME%%\logs\%%BOT%%.log"
echo call pm2 save
echo goto :eof
echo.
echo :start
echo call pm2 start %%BOT%%
echo goto :eof
echo.
echo :stop
echo call pm2 stop %%BOT%%
echo goto :eof
echo.
echo :restart
echo call pm2 restart %%BOT%%
echo goto :eof
echo.
echo :update
echo echo Updating %%BOT%%...
echo cd "%%BOTS_HOME%%\%%BOT%%"
echo git pull
echo pip install -r requirements.txt 2^>nul
echo call pm2 restart %%BOT%%
echo echo %%BOT%% updated and restarted.
echo goto :eof
echo.
echo :remove
echo call pm2 delete %%BOT%%
echo call pm2 save
echo echo %%BOT%% removed from PM2.
echo goto :eof
echo.
echo :list
echo call pm2 list
echo goto :eof
echo.
echo :logs
echo if "%%BOT%%"=="" ^( call pm2 logs --lines 50 ^) else ^( call pm2 logs %%BOT%% --lines 50 ^)
echo goto :eof
echo.
echo :monit
echo call pm2 monit
echo goto :eof
echo.
echo :usage
echo.
echo   Discord Bot Manager
echo   ====================
echo   bot add ^<name^> [entry.py]  - Register and start a bot
echo   bot start ^<name^>           - Start a stopped bot
echo   bot stop ^<name^>            - Stop a running bot
echo   bot restart ^<name^>         - Restart a bot
echo   bot update ^<name^>          - Git pull + reinstall deps + restart
echo   bot remove ^<name^>          - Remove bot from PM2
echo   bot list                   - Show all bots and status
echo   bot logs [name]            - View logs ^(all or specific bot^)
echo   bot monit                  - Live dashboard
echo.
echo   Bots directory: %%BOTS_HOME%%
echo.
echo goto :eof
) > "%BOTS_HOME%\bot.bat"

REM Add bots directory to PATH for this user
echo.
echo Adding bot command to PATH...
setx PATH "%PATH%;%BOTS_HOME%" >nul 2>&1

echo.
echo  ============================================
echo   SETUP COMPLETE
echo  ============================================
echo.
echo  Close and reopen your terminal, then use:
echo.
echo    bot list              - see all bots
echo    bot add my-bot        - register a bot
echo    bot stop my-bot       - stop a bot
echo    bot start my-bot      - start a bot
echo    bot update my-bot     - pull latest + restart
echo    bot logs my-bot       - view logs
echo    bot monit             - live dashboard
echo.
echo  Your first bot (Spice and Dice) is ready.
echo  To register it:
echo    1. Copy or clone it into %BOTS_HOME%\spice-and-dice
echo    2. Run: bot add spice-and-dice bot.py
echo.
pause
