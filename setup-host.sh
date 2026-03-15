#!/usr/bin/env bash
# ============================================================================
#  Discord Bot Host Setup - Linux/macOS (for VPS deployment)
#  Sets up PM2 process manager for running multiple Discord bots
# ============================================================================

set -e

BOTS_HOME="$HOME/discord-bots"

echo ""
echo "  ============================================"
echo "   Discord Bot Hosting Environment Setup"
echo "  ============================================"
echo ""

# --- Step 1: System packages ---
echo "[1/6] Installing system packages..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv git curl
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip git curl
elif command -v yum &>/dev/null; then
    sudo yum install -y python3 python3-pip git curl
elif command -v brew &>/dev/null; then
    brew install python3 git
else
    echo "  WARNING: Unknown package manager. Install python3, pip, git, curl manually."
fi
echo "  OK"

# --- Step 2: Node.js ---
echo ""
echo "[2/6] Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo "  Installing Node.js via nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm install --lts
    nvm use --lts
fi
echo "  OK - Node $(node --version)"

# --- Step 3: PM2 ---
echo ""
echo "[3/6] Installing PM2..."
if ! command -v pm2 &>/dev/null; then
    npm install -g pm2
fi
echo "  OK - PM2 installed"

# --- Step 4: PM2 startup (auto-start on reboot) ---
echo ""
echo "[4/6] Configuring PM2 startup..."
pm2 startup | tail -1 | bash 2>/dev/null || true
echo "  OK"

# --- Step 5: Directory structure ---
echo ""
echo "[5/6] Setting up directory structure..."
mkdir -p "$BOTS_HOME/logs"
echo "  Created $BOTS_HOME"

# --- Step 6: Create bot manager script ---
echo ""
echo "[6/6] Creating bot manager CLI..."

cat > "$BOTS_HOME/bot" << 'BOTSCRIPT'
#!/usr/bin/env bash
# Discord Bot Manager - manages multiple bots via PM2

BOTS_HOME="$HOME/discord-bots"
CMD="$1"
BOT="$2"
ENTRY="${3:-bot.py}"

usage() {
    echo ""
    echo "  Discord Bot Manager"
    echo "  ===================="
    echo "  bot add <name> [entry.py]  - Register and start a bot"
    echo "  bot start <name>           - Start a stopped bot"
    echo "  bot stop <name>            - Stop a running bot"
    echo "  bot restart <name>         - Restart a bot"
    echo "  bot update <name>          - Git pull + reinstall deps + restart"
    echo "  bot remove <name>          - Remove bot from PM2"
    echo "  bot list                   - Show all bots and status"
    echo "  bot logs [name]            - View logs (all or specific bot)"
    echo "  bot monit                  - Live dashboard"
    echo ""
    echo "  Bots directory: $BOTS_HOME"
    echo ""
}

case "$CMD" in
    add)
        [ -z "$BOT" ] && usage && exit 1
        echo "Adding bot: $BOT ($ENTRY)"
        cd "$BOTS_HOME/$BOT"
        if [ -f requirements.txt ]; then
            pip3 install -r requirements.txt --quiet
        fi
        pm2 start "$ENTRY" \
            --name "$BOT" \
            --interpreter python3 \
            --cwd "$BOTS_HOME/$BOT" \
            --log "$BOTS_HOME/logs/$BOT.log" \
            --restart-delay 5000 \
            --max-restarts 10
        pm2 save
        ;;
    start)
        [ -z "$BOT" ] && usage && exit 1
        pm2 start "$BOT"
        ;;
    stop)
        [ -z "$BOT" ] && usage && exit 1
        pm2 stop "$BOT"
        ;;
    restart)
        [ -z "$BOT" ] && usage && exit 1
        pm2 restart "$BOT"
        ;;
    update)
        [ -z "$BOT" ] && usage && exit 1
        echo "Updating $BOT..."
        cd "$BOTS_HOME/$BOT"
        git pull
        if [ -f requirements.txt ]; then
            pip3 install -r requirements.txt --quiet
        fi
        pm2 restart "$BOT"
        echo "$BOT updated and restarted."
        ;;
    remove)
        [ -z "$BOT" ] && usage && exit 1
        pm2 delete "$BOT"
        pm2 save
        echo "$BOT removed from PM2."
        ;;
    list)
        pm2 list
        ;;
    logs)
        if [ -z "$BOT" ]; then
            pm2 logs --lines 50
        else
            pm2 logs "$BOT" --lines 50
        fi
        ;;
    monit)
        pm2 monit
        ;;
    *)
        usage
        ;;
esac
BOTSCRIPT

chmod +x "$BOTS_HOME/bot"

# Add to PATH
if ! grep -q "discord-bots" "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/discord-bots:$PATH"' >> "$HOME/.bashrc"
fi
if ! grep -q "discord-bots" "$HOME/.zshrc" 2>/dev/null; then
    echo 'export PATH="$HOME/discord-bots:$PATH"' >> "$HOME/.zshrc" 2>/dev/null || true
fi

echo ""
echo "  ============================================"
echo "   SETUP COMPLETE"
echo "  ============================================"
echo ""
echo "  Close and reopen your terminal, then:"
echo ""
echo "  To add your first bot:"
echo "    git clone https://github.com/YOU/REPO.git ~/discord-bots/my-bot"
echo "    echo 'DISCORD_TOKEN=your-token' > ~/discord-bots/my-bot/.env"
echo "    bot add my-bot bot.py"
echo ""
echo "  Commands:"
echo "    bot list              - see all bots"
echo "    bot stop my-bot       - stop a bot"
echo "    bot start my-bot      - start a bot"
echo "    bot update my-bot     - git pull + restart"
echo "    bot logs my-bot       - view logs"
echo "    bot monit             - live dashboard"
echo ""
echo "  PM2 will auto-restart bots if they crash"
echo "  and auto-start them on system reboot."
echo ""
