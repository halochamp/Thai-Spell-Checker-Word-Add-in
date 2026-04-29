#!/bin/bash
# start-addin.sh — รัน HTTPS server สำหรับ Word Add-in

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ตรวจสอบ cert
if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
  echo "❌ ไม่พบ certificate กรุณารัน setup-https.sh ก่อน"
  exit 1
fi

# ตรวจสอบ http-server
if ! command -v http-server &> /dev/null; then
  echo "❌ ไม่พบ http-server กรุณารัน: npm install -g http-server"
  exit 1
fi

echo "=== Thai Spell Checker — Add-in Server ==="
echo "🌐 HTTPS server รันที่: https://localhost:3000"
echo "📄 Taskpane: https://localhost:3000/taskpane.html"
echo ""
echo "กด Ctrl+C เพื่อหยุด"
echo ""

http-server . -p 3000 --ssl --cert cert.pem --key key.pem -c-1 --cors
