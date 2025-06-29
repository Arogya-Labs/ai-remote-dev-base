#!/bin/bash

set -e

echo "Installing Claude Code..."

# Install nvm if not present
if ! command -v nvm &> /dev/null; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Install and use Node.js 18+
nvm install --lts
nvm use --lts

# Install Claude Code
npm install -g @anthropic-ai/claude-code

echo "✓ Claude Code installed successfully!"
echo "Run 'claude' to start"