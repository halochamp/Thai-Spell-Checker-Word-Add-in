# checker.py — ตรวจคำผิดด้วย Ollama
# Input:  list of sentence chunks (จาก chunker.py)
# Output: list of error dicts

import json
import re
import httpx
from config import OLLAMA_URL, CHAT_MODEL, TEMPERATURE, REQUEST_TIMEOUT

SYSTEM_PROMPT = """คุณเป็นผู้เชี่ยวชาญด้านการตรวจสอบการสะกดคำ ทำหน้าที่ตรวจสอบข้อความที่มีภาษาไทย ภาษาอังกฤษ และคำทับศัพท์ปนกัน

กฎการตรวจสอบ:
1. ตรวจคำภาษาไทยที่สะกดผิด
2. ตรวจคำภาษาอังกฤษที่สะกดผิด
3. ตรวจคำทับศัพท์ที่ไม่ตรงมาตรฐานราชบัณฑิตยสภา เช่น "คอมพิวเตอร์" ไม่ใช่ "คอมพิวเตอ", "อินเทอร์เน็ต" ไม่ใช่ "อินเตอเน็ต"
4. ข้ามชื่อเฉพาะ (ชื่อคน, ชื่อบริษัท, ชื่อแบรนด์) ที่ไม่ใช่คำผิด
5. ข้ามคำย่อ, ตัวเลข, สัญลักษณ์

ตอบเป็น JSON array เท่านั้น ห้ามมีข้อความอื่น รูปแบบ:
[
  {
    "word": "คำที่ผิด",
    "suggestion": "คำที่ถูกต้อง",
    "type": "thai|english|transliteration"
  }
]

ถ้าไม่พบคำผิด ตอบ: []"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": "ตรวจสอบ: การลงทุนใน คอมพิวเตอ และ อินเตอเน็ต มีความเสี่ยงสูง"
    },
    {
        "role": "assistant",
        "content": '[{"word":"คอมพิวเตอ","suggestion":"คอมพิวเตอร์","type":"transliteration"},{"word":"อินเตอเน็ต","suggestion":"อินเทอร์เน็ต","type":"transliteration"}]'
    },
    {
        "role": "user",
        "content": "ตรวจสอบ: The systm is running normally และระบบทำงานได้ดี"
    },
    {
        "role": "assistant",
        "content": '[{"word":"systm","suggestion":"system","type":"english"}]'
    },
    {
        "role": "user",
        "content": "ตรวจสอบ: ราคาหุ้นวันนี้ปรับตัวขึ้น 2%"
    },
    {
        "role": "assistant",
        "content": '[]'
    }
]


def check_sentences(chunks: list[dict]) -> list[dict]:
    """
    ตรวจคำผิดในแต่ละ sentence chunk

    Args:
        chunks: list of {"text": str, "offset": int} จาก chunker.py

    Returns:
        list of error dicts พร้อม start/end position ใน original text
    """
    all_errors = []

    for chunk in chunks:
        sentence = chunk["text"]
        base_offset = chunk["offset"]

        errors = _check_single_sentence(sentence)

        for error in errors:
            # หา position ของคำผิดใน sentence
            word = error.get("word", "")
            pos = sentence.find(word)
            if pos == -1:
                continue  # ข้ามถ้าหาไม่เจอ

            all_errors.append({
                "word": word,
                "start": base_offset + pos,
                "end": base_offset + pos + len(word),
                "suggestion": error.get("suggestion", ""),
                "sentence": sentence,
                "type": error.get("type", "thai")
            })

    return all_errors


def _check_single_sentence(sentence: str, retry: int = 2) -> list[dict]:
    """ส่ง sentence ให้ Ollama ตรวจ พร้อม retry ถ้า parse JSON ไม่ได้"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_EXAMPLES,
        {"role": "user", "content": f"ตรวจสอบ: {sentence}"}
    ]

    for attempt in range(retry + 1):
        try:
            response = httpx.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": TEMPERATURE}
                },
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()

            # พยายาม parse JSON
            errors = _parse_json_response(content)
            return errors

        except (httpx.HTTPError, KeyError) as e:
            if attempt == retry:
                print(f"[checker] Ollama error after {retry+1} attempts: {e}")
                return []
        except ValueError as e:
            if attempt == retry:
                print(f"[checker] JSON parse error after {retry+1} attempts: {e}")
                return []

    return []


def _parse_json_response(content: str) -> list[dict]:
    """
    Parse JSON จาก LLM response อย่าง robust
    รองรับกรณีที่ LLM ใส่ markdown code block หรือข้อความเกิน
    """
    # ลอง parse ตรงๆ ก่อน
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # ลอง extract JSON array จาก content
    match = re.search(r'\[.*?\]', content, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot parse JSON from: {content[:100]}")
