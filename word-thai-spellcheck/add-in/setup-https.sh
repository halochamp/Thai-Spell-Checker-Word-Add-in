#!/bin/bash
# setup-https.sh — สร้าง self-signed certificate สำหรับ localhost
# รันครั้งเดียวก่อนใช้งาน

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== สร้าง Self-Signed Certificate สำหรับ localhost ==="
echo ""

# สร้าง cert
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null

if [ $? -eq 0 ]; then
  echo "✅ สร้าง certificate เสร็จแล้ว"
  echo "   cert.pem และ key.pem อยู่ใน: $SCRIPT_DIR"
  echo ""
  echo "ขั้นตอนต่อไป:"
  echo "1. เพิ่ม cert.pem เข้า Keychain (macOS):"
  echo "   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain cert.pem"
  echo ""
  echo "2. รัน HTTPS server:"
  echo "   bash start-addin.sh"
else
  echo "❌ สร้าง certificate ไม่สำเร็จ"
  exit 1
fi
