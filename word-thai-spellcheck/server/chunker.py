# chunker.py — แบ่งข้อความเป็น sentences
# Output: list of {"text": str, "offset": int}

import re
from config import MAX_SENTENCE_LENGTH


def chunk_text(text: str) -> list[dict]:
    """
    แบ่ง text เป็น sentences พร้อม offset ใน original text
    แบ่งที่ . ! ? \\n และ ฯ รองรับทั้งภาษาไทยและอังกฤษ

    Returns:
        list of {"text": sentence_text, "offset": start_position_in_original}
    """
    # แบ่งที่ newline และ sentence-ending punctuation
    pattern = r'(?<=[.!?\n])\s*'
    raw_sentences = re.split(pattern, text)

    result = []
    current_offset = 0

    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            current_offset += 1
            continue

        # หา offset จริงใน original text
        idx = text.find(sentence, current_offset)
        if idx == -1:
            idx = current_offset
        offset = idx

        if len(sentence) <= MAX_SENTENCE_LENGTH:
            result.append({"text": sentence, "offset": offset})
        else:
            # ถ้า sentence ยาวเกินไป แบ่งที่ขอบคำ (space)
            result.extend(_split_long_sentence(sentence, offset))

        current_offset = offset + len(sentence)

    # ถ้าไม่มีการแบ่งเลย (ข้อความสั้นไม่มี punctuation) ส่งทั้งก้อน
    if not result and text.strip():
        result.append({"text": text.strip(), "offset": 0})

    return result


def _split_long_sentence(sentence: str, base_offset: int) -> list[dict]:
    """แบ่ง sentence ยาวที่ขอบ space ไม่ตัดกลางคำ"""
    chunks = []
    start = 0

    while start < len(sentence):
        end = start + MAX_SENTENCE_LENGTH

        if end >= len(sentence):
            chunks.append({
                "text": sentence[start:],
                "offset": base_offset + start
            })
            break

        # หา space ก่อนหน้า end เพื่อไม่ตัดกลางคำ
        split_at = sentence.rfind(" ", start, end)
        if split_at == -1 or split_at <= start:
            split_at = end

        chunks.append({
            "text": sentence[start:split_at],
            "offset": base_offset + start
        })
        start = split_at + 1

    return chunks
