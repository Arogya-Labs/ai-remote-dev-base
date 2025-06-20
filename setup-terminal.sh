#!/bin/bash

# Terminal Setup Script
# Sets up oh-my-bash and tmux for consistent terminal experience

set -e

echo "🚀 Setting up terminal environment..."

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

# Install tmux and fzf if not already installed
if ! command -v tmux &> /dev/null; then
    echo "📺 Installing tmux..."
    sudo apt-get install -y tmux
else
    echo "✅ tmux already installed"
fi

if ! command -v fzf &> /dev/null; then
    echo "🔍 Installing fzf (needed for tmux session switching)..."
    sudo apt-get install -y fzf
else
    echo "✅ fzf already installed"
fi

# Install oh-my-bash (preserving existing .bashrc)
if [ ! -d "$HOME/.oh-my-bash" ]; then
    echo "🎨 Installing oh-my-bash..."
    
    # Backup existing .bashrc before oh-my-bash installation
    if [ -f "$HOME/.bashrc" ]; then
        echo "💾 Backing up existing .bashrc..."
        cp "$HOME/.bashrc" "$HOME/.bashrc.pre-omb.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Install oh-my-bash with --unattended flag to prevent automatic .bashrc replacement
    bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmybash/oh-my-bash/master/tools/install.sh)" "" --unattended
    
    # Restore original .bashrc and manually integrate oh-my-bash
    BACKUP_FILE=$(ls -t "$HOME/.bashrc.pre-omb."* 2>/dev/null | head -1)
    if [ -f "$BACKUP_FILE" ]; then
        echo "🔄 Restoring original .bashrc and integrating oh-my-bash..."
        mv "$BACKUP_FILE" "$HOME/.bashrc"
        
        # Add oh-my-bash initialization to existing .bashrc
        if ! grep -q "source.*oh-my-bash.sh" "$HOME/.bashrc"; then
            cat >> "$HOME/.bashrc" << 'EOF'

# Initialize oh-my-bash
export OSH="$HOME/.oh-my-bash"
export OSH_THEME="agnoster"
source "$OSH/oh-my-bash.sh"
EOF
        fi
    fi
else
    echo "✅ oh-my-bash already installed"
fi

# Setup tmux configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMUX_CONF_SOURCE="$SCRIPT_DIR/tmux.conf"

if [ -f "$TMUX_CONF_SOURCE" ]; then
    if [ ! -f "$HOME/.tmux.conf" ]; then
        echo "⚙️ Copying tmux configuration..."
        cp "$TMUX_CONF_SOURCE" "$HOME/.tmux.conf"
        echo "✅ tmux configuration installed"
    else
        echo "⚠️  tmux configuration already exists. Backing up and installing new config..."
        cp "$HOME/.tmux.conf" "$HOME/.tmux.conf.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$TMUX_CONF_SOURCE" "$HOME/.tmux.conf"
        echo "✅ tmux configuration updated (backup created)"
    fi
    
    # Install tmux plugin manager if not already installed
    if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
        echo "🔌 Installing tmux plugin manager..."
        git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
        echo "✅ tmux plugin manager installed"
        echo "ℹ️  Run 'tmux' then press 'prefix + I' to install plugins"
    else
        echo "✅ tmux plugin manager already installed"
    fi
else
    echo "❌ tmux.conf not found in script directory"
    exit 1
fi

# Set oh-my-bash theme and plugins in .bashrc if not already configured
if ! grep -q "OSH_THEME=" "$HOME/.bashrc" 2>/dev/null || ! grep -q "agnoster" "$HOME/.bashrc" 2>/dev/null; then
    echo "🎨 Configuring oh-my-bash theme..."
    
    # Backup existing .bashrc
    cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update oh-my-bash theme to agnoster (similar to oh-my-zsh)
    sed -i 's/OSH_THEME=".*"/OSH_THEME="agnoster"/' "$HOME/.bashrc" 2>/dev/null || true
    
    # Add some useful aliases if they don't exist
    if ! grep -q "# Custom aliases" "$HOME/.bashrc"; then
        cat >> "$HOME/.bashrc" << 'EOF'

# Custom aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias tmux='tmux -2'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline'

# ── Tmux aliases ────────────────────────────────────────────────────────
alias tks='tmux kill-session -t'       # tks session-name
alias tkill='tmux kill-server'         # Kill all sessions  
alias tls='tmux list-sessions'         # List sessions
alias ta='tmux attach-session -t'      # ta session-name
alias tn='tmux new-session -s'         # tn session-name
alias td='tmux detach'                 # Detach current session

tms() {
  tmux switch-client -t "$(tmux list-sessions -F '#S' | fzf)"
}
EOF
    fi
    
    echo "✅ oh-my-bash configured with agnoster theme"
else
    echo "✅ oh-my-bash already configured"
fi

# Add tmux auto-start if not already present
if ! grep -q "Auto-start tmux for interactive non-login shells" "$HOME/.bashrc"; then
    echo "⚙️ Adding tmux auto-start to .bashrc..."
    cat >> "$HOME/.bashrc" << 'EOF'

# Auto-start tmux for interactive non-login shells
if [[ $- == *i* ]] && [[ -z "$TMUX" ]] && [[ -n "$SSH_CONNECTION" ]]; then
    # Create a unique session name based on timestamp
    session_name="session-$(date +%s)"
    tmux new-session -s "$session_name"
fi
EOF
    echo "✅ tmux auto-start added"
else
    echo "⚙️ Updating existing tmux auto-start to create new sessions..."
    # Remove old auto-start section and add new one
    sed -i '/# Auto-start tmux for interactive non-login shells/,/^fi$/d' "$HOME/.bashrc"
    cat >> "$HOME/.bashrc" << 'EOF'

# Auto-start tmux for interactive non-login shells
if [[ $- == *i* ]] && [[ -z "$TMUX" ]] && [[ -n "$SSH_CONNECTION" ]]; then
    # Create a unique session name based on timestamp
    session_name="session-$(date +%s)"
    tmux new-session -s "$session_name"
fi
EOF
    echo "✅ tmux auto-start updated to create new sessions"
fi

echo ""
echo "🎉 Terminal setup complete!"
echo ""
echo "To start using:"
echo "  • Reload your shell: source ~/.bashrc"
echo "  • tmux will auto-start new sessions on SSH connections"
echo "  • Install tmux plugins: prefix + I (default prefix is Ctrl-b)"
echo ""
echo "Key features from your tmux config:"
echo "  • Mouse support enabled"
echo "  • Vim-style pane navigation (prefix + h/j/k/l)"
echo "  • Vim-style pane resizing (prefix + H/J/K/L)"  
echo "  • Session management (prefix + C-n for new session)"
echo "  • Plugins: tmux-sensible, tmux-yank, tmux-sessionist"
echo ""
echo "Tmux aliases available:"
echo "  • tks <session>   - Kill session"
echo "  • tkill          - Kill all sessions"
echo "  • tls            - List sessions"
echo "  • ta <session>   - Attach to session"
echo "  • tn <session>   - New session"
echo "  • td             - Detach current session"
echo "  • tms            - Interactive session switcher (uses fzf)"
echo ""