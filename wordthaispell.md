# Thai Spell Checker — Word Add-in
## โครงสร้างโปรเจค v1.0

> **วัตถุประสงค์:** Word Add-in ตรวจคำผิดภาษาไทย, อังกฤษ, และทับศัพท์ด้วย Local AI (Ollama)  
> ทำงาน offline 100% ไม่มี external API  
> แจกจ่ายสาธารณะ — ผู้ใช้ติดตั้งเองได้

---

## 🚦 Quick Status

### สถานะปัจจุบัน
- ✅ เขียน code ครบทุกไฟล์ตาม spec
- ✅ Python server (FastAPI + Ollama) ทำงานได้
- ✅ ทดสอบ `/check` ตรวจคำผิดได้จริง (ทับศัพท์ถูกต้องตามราชบัณฑิตยสภา)
- ✅ HTTPS add-in server รันที่ localhost:3000
- ✅ Self-signed certificate trust แล้วใน macOS Keychain
- 🔴 ติดตั้ง Add-in ใน Word — ยังไม่ได้ทำ (upload manifest ไม่ได้)

### การตัดสินใจสำคัญ
- **Sentence chunk** แทน paragraph chunk — ป้องกันตัดกลางคำ
- **On-demand** (กดปุ่ม) แทน real-time — LLM ช้าเกินไปสำหรับ real-time
- **ตรวจคำผิดอย่างเดียว** — ไม่มี auto-fix, ไม่มี grammar check
- **รองรับข้อความผสม** — ไทย, อังกฤษ, และทับศัพท์ในเอกสารเดียวกัน
- **มาตรฐานทับศัพท์** — ใช้เกณฑ์ราชบัณฑิตยสภาเป็นหลัก
- **แจกจ่ายสาธารณะ** — ต้องมี install script ที่ใช้งานง่าย

---

## โครงสร้างไฟล์

```
word-thai-spellcheck/
├── README.md
├── add-in/
│   ├── manifest.xml       ← บอก Word ว่า Add-in คืออะไร (sideload)
│   ├── taskpane.html      ← UI panel ด้านข้างใน Word
│   ├── taskpane.js        ← logic หลัก (Office.js)
│   └── taskpane.css       ← style
└── server/
    ├── main.py            ← FastAPI app + endpoints
    ├── checker.py         ← spell check logic หลัก
    ├── chunker.py         ← sentence tokenizer (PyThaiNLP)
    ├── config.py          ← ค่าคงที่ (model, port, threshold)
    ├── requirements.txt
    ├── install.sh         ← script ติดตั้ง (macOS/Linux)
    └── install.bat        ← script ติดตั้ง (Windows)
```

---

## Architecture

```
Microsoft Word
    ↓ กดปุ่ม "ตรวจสอบ"
add-in/taskpane.js (Office.js)
    ↓ ดึง text จาก document
    ↓ POST /check
server/main.py (FastAPI — localhost:8000)
    ↓
server/chunker.py
    PyThaiNLP sent_tokenize() → list of sentences
    ↓
server/checker.py
    loop แต่ละ sentence → Ollama API (localhost:11434)
    ↓ qwen2.5:3b หรือ gemma4:e4b
    รวมผลลัพธ์ → list ของ errors
    ↓
taskpane.js รับ response
    ↓
Office.js highlight คำผิด (สีแดง) ใน document
    ↓
แสดงสรุป "พบ N คำที่ควรตรวจสอบ"
```

---

## Module Responsibilities

### `server/config.py`
ค่าคงที่ทั้งหมด ไม่มี logic

| Variable | Default | หมายเหตุ |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API |
| `CHAT_MODEL` | `qwen2.5:3b` | เปลี่ยนได้ |
| `SERVER_PORT` | `8000` | FastAPI port |
| `MAX_SENTENCE_LENGTH` | `500` | chars ต่อ sentence |
| `REQUEST_TIMEOUT` | `30` | วินาที |
| `TEMPERATURE` | `0.1` | ต่ำ = consistent |

---

### `server/chunker.py`
แบ่งข้อความเป็น sentences ด้วย PyThaiNLP

**Input:** text ทั้งย่อหน้า  
**Output:** `list[str]` — list of sentences

**Logic:**
- ใช้ `pythainlp.tokenize.sent_tokenize()`
- ถ้า sentence ยาวเกิน `MAX_SENTENCE_LENGTH` → แบ่งที่ขอบคำ (ไม่ตัดกลางคำ)
- คืน list พร้อม offset ของแต่ละ sentence ใน text ต้นฉบับ

---

### `server/checker.py`
ตรวจคำผิดด้วย Ollama

**Input:** `list[str]` sentences + original text  
**Output:** `list[dict]` errors

```
error format:
{
  "word":       "กาน",
  "start":      10,      ← position ใน original text
  "end":        13,
  "suggestion": "การ",
  "sentence":   "กาน ลงทุน...",
  "type":       "thai" | "english" | "transliteration"
}
```

**Prompt strategy:**
- Few-shot prompt ภาษาไทย
- บอก LLM ให้ตรวจทั้งคำไทย, คำอังกฤษ, และทับศัพท์
- ทับศัพท์ใช้มาตรฐานราชบัณฑิตยสภา เช่น "คอมพิวเตอร์" ไม่ใช่ "คอมพิวเตอ", "อินเทอร์เน็ต" ไม่ใช่ "อินเตอเน็ต"
- บอก LLM ให้ระบุ `type` ของ error ด้วยทุกครั้ง
- บอก LLM ให้คืน JSON เท่านั้น
- Temperature 0.1 เพื่อ consistency
- Retry 2 ครั้งถ้า parse JSON ไม่ได้

**Position mapping:**
- แต่ละ sentence รู้ offset ใน original text
- error position = sentence offset + position ใน sentence

---

### `server/main.py`
FastAPI server

**Endpoints:**

```
POST /check
  Body:    {"text": "ข้อความทั้งหมด"}
  Response: {"errors": [...], "total": N, "time_seconds": X.X}

GET /health
  Response: {"status": "ok", "model": "qwen2.5:3b", "ollama": true/false}

GET /models
  Response: {"available": ["qwen2.5:3b", "gemma4:e4b", ...]}
```

**CORS:** เปิดให้ localhost เท่านั้น (ความปลอดภัย)

---

### `add-in/manifest.xml`
บอก Word ว่า Add-in คืออะไร

- ชื่อ: "Thai Spell Checker"
- Permission: ReadWriteDocument (อ่านและ highlight ได้)
- URL: `https://localhost:3000/taskpane.html`

---

### `add-in/taskpane.js`
Logic หลักฝั่ง Word

**Flow:**
```
1. กดปุ่ม "ตรวจสอบ"
2. Office.js: context.document.body.load("text")
3. ส่ง POST /check
4. รับ errors list
5. loop: Office.js search + highlight แต่ละคำผิด
6. แสดง progress bar ระหว่างรอ
7. แสดงสรุปผล
```

**UI elements:**
- ปุ่ม "ตรวจสอบ"
- ปุ่ม "ล้าง highlight"
- Progress bar
- สรุป: "พบ N คำที่ควรตรวจสอบ"
- Status bar: แสดง "Ollama · {model name}" และเวลาที่ใช้
- Footer: "พัฒนาโดย Poomwat — The Generalist Investor · www.poomwat.com"

---

## Dependencies

### Python (server)
```
fastapi
uvicorn
pythainlp
ollama
```

### JavaScript (add-in)
```
Office.js  ← CDN ไม่ต้องติดตั้ง
```

### Ollama Models
```
# แนะนำ dev
ollama pull qwen2.5:3b

# แนะนำ production (เครื่อง RAM 16GB+)
ollama pull gemma4:e4b
```

---

## ขั้นตอนติดตั้งสำหรับผู้ใช้

```
1. ติดตั้ง Ollama จาก https://ollama.ai
2. รัน: ollama pull qwen2.5:3b
3. รัน: install.sh (macOS) หรือ install.bat (Windows)
4. รัน: python server/main.py
5. เปิด Word → Insert → Add-ins → Upload manifest.xml
6. พร้อมใช้งาน
```

---

## สิ่งที่ไม่ทำ (Out of Scope)

```
❌ Auto-fix คำผิด
❌ Grammar check
❌ Style suggestion
❌ Real-time check ขณะพิมพ์
❌ Database / history
❌ User accounts
❌ Cloud / external API
```

---

## Known Challenges

| ความท้าทาย | วิธีรับมือ |
|---|---|
| Position mapping ใน Word | ใช้ Office.js `search()` หาคำแล้ว highlight |
| ชื่อเฉพาะถูก flag ผิด | เพิ่ม whitelist / custom dictionary |
| LLM ตอบไม่เป็น JSON | Retry 2 ครั้ง + robust parser |
| Ollama ไม่ได้รัน | `/health` endpoint แจ้งเตือนก่อนตรวจ |
| เอกสารยาวมาก | Progress bar + ยกเลิกได้กลางทาง |
| ทับศัพท์มีหลายรูปแบบที่ยอมรับได้ | ใช้มาตรฐานราชบัณฑิตยสภาเป็น ground truth, เพิ่ม whitelist สำหรับคำที่ยอมรับหลายรูปแบบ |
| คำอังกฤษในบริบทไทยถูก flag ผิด | Prompt บอก LLM ให้ตรวจ context ก่อน flag คำอังกฤษ |

---

## แผนการพัฒนา (4 เฟส)

| เฟส | งาน | เวลาประมาณ |
|---|---|---|
| 1 | Backend Core — `config.py`, `chunker.py`, `checker.py` + ทดสอบด้วย curl | 1-2 วัน |
| 2 | FastAPI Server — `main.py`, endpoints `/check` `/health` `/models`, CORS | 1 วัน |
| 3 | Word Add-in UI — `manifest.xml`, `taskpane.html/js/css`, highlight คำผิด | 3-5 วัน |
| 4 | Polish & Distribution — `install.sh`, `install.bat`, `README.md`, ทดสอบจริง | 1-2 วัน |

**รวมประมาณ:** 6-10 วัน (เขียนเอง) / 2-3 วัน (ใช้ AI ช่วย)

**ความเสี่ยง:** Prompt tuning, Position mapping offset, Self-signed cert สำหรับ localhost HTTPS

---

## การ Deploy / แจกจ่าย

- ใช้วิธี **Sideload** — ผู้ใช้ upload `manifest.xml` เองใน Word (Insert → Add-ins)
- **ไม่ต้อง** deploy ผ่าน Microsoft Store หรือสมัคร developer account
- Add-in โหลดจาก `localhost:3000` ในเครื่องผู้ใช้เอง
- ข้อจำกัด: ต้องมี self-signed cert สำหรับ HTTPS, ใช้ได้เฉพาะ Word Desktop

---

## Session Log

| วันที่ | ทำอะไร |
|---|---|
| 28 Apr 2026 | วิเคราะห์ความเป็นไปได้ |
| 28 Apr 2026 | ตัดสินใจ architecture: Word Add-in + FastAPI + Ollama |
| 28 Apr 2026 | เลือก Sentence chunk แทน Paragraph chunk |
| 28 Apr 2026 | ออกแบบโครงสร้างโปรเจค |
| 29 Apr 2026 | เพิ่ม scope: รองรับข้อความไทยผสมอังกฤษและทับศัพท์ |
| 29 Apr 2026 | เพิ่ม error type field, อัปเดต prompt strategy, เพิ่ม Known Challenges |
| 29 Apr 2026 | เพิ่ม UI: status bar แสดง model, footer เครดิตผู้พัฒนา |
| 29 Apr 2026 | เพิ่มแผน 4 เฟส, ประมาณเวลา, และข้อมูลการ deploy แบบ sideload |
| 29 Apr 2026 | สร้างโปรเจคครบทุกไฟล์: server/ และ add-in/ |
| 29 Apr 2026 | ติดตั้ง dependencies, รัน server สำเร็จ |
| 29 Apr 2026 | พบ bug: chunker.py ใช้ crfcut engine ที่ต้องการ pycrfsuite — แก้เป็น regex แทน |
| 29 Apr 2026 | ทดสอบ /check endpoint สำเร็จ — ตรวจ "คอมพิวเตอ"→"คอมพิวเตอร์", "อินเตอเน็ต"→"อินเทอร์เน็ต" ได้ถูกต้อง |
| 29 Apr 2026 | สร้าง self-signed cert, trust ใน macOS Keychain, รัน HTTPS server ที่ localhost:3000 สำเร็จ |
| 29 Apr 2026 | หยุดที่เฟส 3 — ติดปัญหา upload manifest.xml ใน Word |

## ความคืบหน้าเฟส

| เฟส | สถานะ | หมายเหตุ |
|---|---|---|
| 1 Backend Core | ✅ เสร็จ | แก้ bug chunker engine แล้ว |
| 2 FastAPI Server | ✅ เสร็จ | ทดสอบ /check /health /models ผ่านแล้ว |
| 3 Word Add-in UI | 🔴 ค้างอยู่ | HTTPS server พร้อม แต่ upload manifest ใน Word ไม่ได้ |
| 4 Polish & Distribution | ⏳ ยังไม่เริ่ม | |
