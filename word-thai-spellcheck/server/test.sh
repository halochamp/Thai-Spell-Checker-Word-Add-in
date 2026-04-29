#!/bin/bash
curl -s -X POST http://127.0.0.1:8000/check \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"การลงทุนใน คอมพิวเตอ และ อินเตอเน็ต มีความเสี่ยงสูง.\"}" \
  | python3 -m json.tool
