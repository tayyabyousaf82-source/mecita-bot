"""
FastAPI server — serves form.html and receives booking requests.
"""
import logging
import os
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from bcncita import CustomerProfile, DocType, Office, OperationType, Province, try_cita

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

app = FastAPI()

# Secret token to protect the API
API_SECRET = os.getenv("API_SECRET", "")

# Track if bot is currently running
bot_running = False


class BookingRequest(BaseModel):
    secret: str
    province: str
    operation_code: str
    doc_type: str
    doc_value: str
    name: str
    year_of_birth: Optional[str] = None
    phone: str
    email: str
    country: str = "ANGOLA"
    offices: Optional[list] = []
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    cycles: int = 200


@app.get("/", response_class=HTMLResponse)
async def serve_form():
    html_path = os.path.join(os.path.dirname(__file__), "form.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/book")
async def book(req: BookingRequest):
    global bot_running

    # Auth check
    if API_SECRET and req.secret != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

    if bot_running:
        return JSONResponse({"status": "error", "message": "Bot already running!"})

    # Map strings to enums
    try:
        province = Province[req.province]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid province: {req.province}")

    try:
        operation = OperationType[req.operation_code]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {req.operation_code}")

    try:
        doc_type = DocType[req.doc_type]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid doc_type: {req.doc_type}")

    offices = []
    for o in req.offices:
        try:
            offices.append(Office[o])
        except KeyError:
            pass

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    customer = CustomerProfile(
        anticaptcha_api_key=os.getenv("2CAPTCHA_API_KEY") or None,
        auto_captcha=True,
        auto_office=not bool(offices),
        chrome_driver_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"),
        save_artifacts=False,
        province=province,
        operation_code=operation,
        doc_type=doc_type,
        doc_value=req.doc_value,
        country=req.country,
        name=req.name,
        year_of_birth=req.year_of_birth,
        phone=req.phone,
        email=req.email,
        min_date=req.min_date,
        max_date=req.max_date,
        telegram_token=token,
        telegram_chat_id=chat_id,
        offices=offices,
    )

    def run():
        global bot_running
        bot_running = True
        try:
            try_cita(context=customer, cycles=req.cycles)
        except Exception as e:
            logging.error(f"Cita bot error: {e}")
            import requests as req_lib
            if token and chat_id:
                req_lib.get(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    params={"chat_id": chat_id, "text": f"❌ Bot error: {e}"},
                    timeout=10,
                )
        finally:
            bot_running = False

    threading.Thread(target=run, daemon=True).start()
    return JSONResponse({"status": "ok", "message": "Bot started! Telegram pe notification milegi."})


@app.get("/status")
async def status():
    return JSONResponse({"running": bot_running})
