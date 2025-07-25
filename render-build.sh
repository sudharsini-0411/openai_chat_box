#!/usr/bin/env bash
set -e

echo "Installing Ollama CLI..."
curl -fsSL https://ollama.com/download/Ollama-linux-amd64 -o ollama
chmod +x ollama
sudo mv ollama /usr/local/bin/

echo "✅ Ollama installed successfully!"
