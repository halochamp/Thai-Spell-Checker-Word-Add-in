#!/bin/bash
# install.sh — ติดตั้ง Thai Spell Checker Server (macOS / Linux)

set -e

echo "=== Thai Spell Checker — Server Setup ==="
echo ""

# ตรวจสอบ Python
if ! command -v python3 &> /dev/null; then
    echo "❌ ไม่พบ Python 3 กรุณาติดตั้งก่อน: https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION"

# ตรวจสอบ Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ ไม่พบ Ollama กรุณาติดตั้งก่อน: https://ollama.ai"
    exit 1
fi
echo "✅ Ollama พบแล้ว"

# สร้าง virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "📦 สร้าง virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 ติดตั้ง dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "✅ ติดตั้งเสร็จแล้ว!"
echo ""
echo "วิธีรัน server:"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "หรือรันตรงๆ:"
echo "  $(pwd)/venv/bin/python $(pwd)/main.py"
