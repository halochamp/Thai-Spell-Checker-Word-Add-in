# Thai Spell Checker — Word Add-in

> ตรวจคำผิดภาษาไทย, อังกฤษ, และทับศัพท์ใน Microsoft Word ด้วย AI ในเครื่องของคุณ  
> ทำงาน offline 100% — ไม่มีข้อมูลออกนอกเครื่อง

![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey)
![Offline](https://img.shields.io/badge/AI-Local%20%2F%20Offline-green)

---

## 📖 เกี่ยวกับโปรเจค

Thai Spell Checker เป็น Add-in สำหรับ Microsoft Word ที่ช่วยตรวจสอบการสะกดคำในเอกสารภาษาไทย รองรับข้อความที่ผสมทั้งภาษาไทย, ภาษาอังกฤษ, และคำทับศัพท์ในเอกสารเดียวกัน

จุดเด่นที่แตกต่างจากเครื่องมืออื่น คือใช้ **Local AI ผ่าน Ollama** ทำงานในเครื่องของคุณทั้งหมด ข้อมูลในเอกสารไม่ถูกส่งออกไปยัง server ภายนอกหรือ cloud ใดๆ เหมาะสำหรับเอกสารที่มีความลับหรือข้อมูลสำคัญ

เมื่อกดปุ่ม "ตรวจสอบ" Add-in จะดึงข้อความจากเอกสาร แบ่งเป็นประโยค ส่งให้ AI วิเคราะห์ทีละประโยค แล้ว highlight คำที่สะกดผิดสีแดงในเอกสารโดยตรง พร้อมแสดงคำแนะนำที่ถูกต้อง

---

## ✨ ฟีเจอร์หลัก

- ✅ ตรวจคำผิด**ภาษาไทย**
- ✅ ตรวจคำผิด**ภาษาอังกฤษ**
- ✅ ตรวจ**ทับศัพท์**ตามมาตรฐานราชบัณฑิตยสภา เช่น "คอมพิวเตอร์", "อินเทอร์เน็ต"
- ✅ รองรับ**ข้อความผสม**ไทย-อังกฤษในเอกสารเดียวกัน
- ✅ **Highlight** คำผิดสีแดงใน Word โดยตรง
- ✅ ทำงาน **offline** ด้วย Ollama — ไม่ส่งข้อมูลออกนอกเครื่อง
- ✅ **ไม่ต้อง** สมัคร account หรือจ่ายค่า API

---

## 🖥️ Requirements

| Software | Version |
|---|---|
| Microsoft Word | Desktop (Windows / macOS) |
| Python | 3.9+ |
| [Ollama](https://ollama.ai) | Latest |

**Ollama Model (เลือกอย่างน้อย 1 ตัว):**

```bash
# แนะนำสำหรับเครื่องทั่วไป (RAM 8GB+)
ollama pull qwen2.5:3b

# แนะนำสำหรับเครื่องแรง (RAM 16GB+)
ollama pull gemma4:e4b
```

---

## 🚀 ติดตั้ง

### macOS / Linux

```bash
git clone https://github.com/your-username/word-thai-spellcheck.git
cd word-thai-spellcheck
bash server/install.sh
```

### Windows

```bat
git clone https://github.com/your-username/word-thai-spellcheck.git
cd word-thai-spellcheck
server\install.bat
```

---

## ▶️ วิธีใช้งาน

**1. เริ่ม server**

```bash
python server/main.py
```

Server จะรันที่ `http://localhost:8000`

**2. ติดตั้ง Add-in ใน Word**

```
Word → Insert → Add-ins → Upload a My Add-in → เลือก add-in/manifest.xml
```

**3. ตรวจสอบเอกสาร**

- เปิด panel "Thai Spell Checker" ด้านข้าง
- กดปุ่ม **"ตรวจสอบ"**
- คำผิดจะถูก highlight สีแดงในเอกสาร
- กด **"ล้าง highlight"** เมื่อต้องการล้าง

---

## 🏗️ Architecture

```
Microsoft Word
    ↓ กดปุ่ม "ตรวจสอบ"
add-in/taskpane.js  (Office.js)
    ↓ POST /check
server/main.py  (FastAPI — localhost:8000)
    ↓
server/chunker.py  →  PyThaiNLP sent_tokenize()
    ↓
server/checker.py  →  Ollama API (localhost:11434)
    ↓
taskpane.js  →  highlight คำผิดใน Word
```

---

## 📁 โครงสร้างโปรเจค

```
word-thai-spellcheck/
├── README.md
├── add-in/
│   ├── manifest.xml       ← Add-in manifest สำหรับ sideload
│   ├── taskpane.html      ← UI panel
│   ├── taskpane.js        ← Office.js logic
│   └── taskpane.css       ← Style
└── server/
    ├── main.py            ← FastAPI endpoints
    ├── checker.py         ← Spell check + Ollama
    ├── chunker.py         ← Sentence tokenizer
    ├── config.py          ← ค่าคงที่
    ├── requirements.txt
    ├── install.sh
    └── install.bat
```

---

## 🔌 API Endpoints

| Method | Endpoint | คำอธิบาย |
|---|---|---|
| `POST` | `/check` | ตรวจคำผิดในข้อความ |
| `GET` | `/health` | ตรวจสอบสถานะ server และ Ollama |
| `GET` | `/models` | ดู model ที่ติดตั้งใน Ollama |

**ตัวอย่าง response `/check`:**

```json
{
  "errors": [
    {
      "word": "คอมพิวเตอ",
      "start": 5,
      "end": 14,
      "suggestion": "คอมพิวเตอร์",
      "type": "transliteration"
    }
  ],
  "total": 1,
  "time_seconds": 2.3
}
```

`type` มี 3 ค่า: `"thai"` | `"english"` | `"transliteration"`

---

## ❌ Out of Scope

สิ่งที่โปรเจคนี้**ไม่ทำ**โดยตั้งใจ:

- Auto-fix คำผิด
- Grammar check
- Real-time check ขณะพิมพ์
- Cloud / external API
- User accounts / history

---

## 🛠️ Dependencies

**Python**
```
fastapi
uvicorn
pythainlp
ollama
```

**JavaScript**
```
Office.js  (CDN — ไม่ต้องติดตั้ง)
```

---

## 👤 ผู้พัฒนา

**Poomwat — The Generalist Investor**  
🌐 [www.poomwat.com](https://www.poomwat.com)

---

## 📄 License

MIT License — ใช้งานและแจกจ่ายได้อย่างอิสระ
