# main.py — FastAPI server
# รันด้วย: python main.py

import time
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import OLLAMA_URL, CHAT_MODEL, SERVER_PORT
from chunker import chunk_text
from checker import check_sentences

app = FastAPI(title="Thai Spell Checker", version="1.0.0")

# CORS — เปิดให้ localhost เท่านั้น
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:3000",
        "http://localhost:3000",
        "null",  # สำหรับ file:// sideload
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Request / Response Models ---

class CheckRequest(BaseModel):
    text: str


class CheckResponse(BaseModel):
    errors: list[dict]
    total: int
    time_seconds: float


class HealthResponse(BaseModel):
    status: str
    model: str
    ollama: bool


class ModelsResponse(BaseModel):
    available: list[str]


# --- Endpoints ---

@app.post("/check", response_model=CheckResponse)
async def check_text(req: CheckRequest):
    """ตรวจคำผิดในข้อความ"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text ต้องไม่ว่างเปล่า")

    start_time = time.time()

    # แบ่งเป็น sentences
    chunks = chunk_text(req.text)

    # ตรวจแต่ละ sentence
    errors = check_sentences(chunks)

    elapsed = round(time.time() - start_time, 2)

    return CheckResponse(
        errors=errors,
        total=len(errors),
        time_seconds=elapsed
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ตรวจสอบสถานะ server และ Ollama"""
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        ollama_ok = False

    return HealthResponse(
        status="ok",
        model=CHAT_MODEL,
        ollama=ollama_ok
    )


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """ดู model ที่ติดตั้งใน Ollama"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return ModelsResponse(available=models)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ไม่สามารถเชื่อมต่อ Ollama: {e}")


# --- Run ---

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=SERVER_PORT, reload=False)
