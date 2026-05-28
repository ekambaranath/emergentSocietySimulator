#!/bin/bash
# setup.sh — run once after unzipping in Codespaces
# Usage: bash setup.sh

set -e

echo "🧬 Emergent Society Simulator — Setup"
echo "══════════════════════════════════════"

# 1. Python deps
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt -q

# 2. Frontend deps
echo ""
echo "⚛️  Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

# 3. .env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env (OLLAMA_HOST=http://localhost:11434)"
fi

# 4. Install Ollama if not present
if ! command -v ollama &> /dev/null; then
  echo ""
  echo "🦙 Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "✅ Ollama already installed: $(ollama --version)"
fi

# 5. Pull default model
echo ""
echo "🦙 Pulling llama3.1 model (this may take a few minutes on first run)..."
ollama pull llama3.1

echo ""
echo "══════════════════════════════════════"
echo "✅ Setup complete! To run:"
echo ""
echo "  Terminal 1 (Ollama):"
echo "    ollama serve"
echo ""
echo "  Terminal 2 (backend):"
echo "    python main.py"
echo ""
echo "  Terminal 3 (frontend):"
echo "    cd frontend && npm run dev"
echo ""
echo "  Open: http://localhost:5173"
echo ""
echo "  💡 To change model, edit config.py → AIConfig.model"
echo "     Any Ollama model works: mistral, gemma2, phi3, etc."
echo "══════════════════════════════════════"
