"""
booking.py — Full auto-booking engine
Features:
  - 2Captcha integration (base64 image solve)
  - OTP handling via Spanish phone
  - PDF download of confirmation
  - 24/7 retry with date range filtering
"""
import asyncio, logging, base64, httpx, os, re
from datetime import datetime, date
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from config import BOOKING_URL, HEADLESS, CAPTCHA_API_KEY, SPANISH_PHONE
from data import PROVINCIA_DATA

logger = logging.getLogger(__name__)

# ─── 2Captcha ─────────────────────────────────────────────────────────────────

async def solve_captcha_image(img_bytes: bytes) -> str:
    """Send base64 image to 2captcha and return solution text"""
    if not CAPTCHA_API_KEY:
        logger.warning("No 2Captcha API key set")
        return ""
    b64 = base64.b64encode(img_bytes).decode()
    async with httpx.AsyncClient(timeout=120) as client:
        # Submit captcha
        r = await client.post("https://2captcha.com/in.php", data={
            "key":    CAPTCHA_API_KEY,
            "method": "base64",
            "body":   b64,
            "json":   1,
        })
        data = r.json()
        if data.get("status") != 1:
            logger.error(f"2Captcha submit error: {data}")
            return ""
        captcha_id = data["request"]
        logger.info(f"2Captcha ID: {captcha_id} — waiting for solution...")

        # Poll for result
        for _ in range(20):
            await asyncio.sleep(5)
            res = await client.get("https://2captcha.com/res.php", params={
                "key":    CAPTCHA_API_KEY,
                "action": "get",
                "id":     captcha_id,
                "json":   1,
            })
            rd = res.json()
            if rd.get("status") == 1:
                logger.info(f"2Captcha solved: {rd['request']}")
                return rd["request"]
            if rd.get("request") != "CAPCHA_NOT_READY":
                logger.error(f"2Captcha error: {rd}")
                return ""
    return ""

# ─── PDF Download ─────────────────────────────────────────────────────────────

async def save_confirmation_pdf(page, booking_id: str) -> str:
    """Save current page as PDF and return file path"""
    os.makedirs("pdfs", exist_ok=True)
    path = f"pdfs/cita_{booking_id}.pdf"
    await page.pdf(path=path, format="A4", print_background=True)
    logger.info(f"PDF saved: {path}")
    return path

# ─── OTP Wait ─────────────────────────────────────────────────────────────────

async def wait_for_otp(bot, chat_id: int, booking_id: str, db, timeout=120) -> str:
    """
    Ask user to forward OTP, wait for it via bot message handler.
    Returns OTP string or empty string on timeout.
    """
    await bot.send_message(
        chat_id,
        f"📱 *Se ha enviado un SMS al número español registrado.*\n\n"
        f"Por favor escribe el código OTP que has recibido:\n"
        f"_(Tienes {timeout//60} minutos)_",
        parse_mode="Markdown"
    )
    # Poll DB for OTP saved by bot handler
    for _ in range(timeout // 3):
        await asyncio.sleep(3)
        otp_row = db.get_pending_otp(booking_id)
        if otp_row:
            db.mark_otp_used(booking_id)
            return otp_row["otp_code"]
    return ""

# ─── Date Range Check ─────────────────────────────────────────────────────────

def is_date_in_range(date_str: str, date_from: str, date_to: str) -> bool:
    """Check if DD/MM/YYYY date is within YYYY-MM-DD range"""
    if not date_str or not date_from or not date_to:
        return True
    try:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", date_str)
        if not m:
            return True
        d, mo, y = m.groups()
        slot_date = date(int(y), int(mo), int(d))
        from_date = date.fromisoformat(date_from)
        to_date   = date.fromisoformat(date_to)
        return from_date <= slot_date <= to_date
    except Exception:
        return True

# ─── Main Booking ─────────────────────────────────────────────────────────────

async def book_appointment(data: dict, bot=None, db=None) -> dict:
    """
    Full booking flow with 2captcha + OTP + PDF + date range
    """
    province_id = data["province_id"]
    tramite_id  = data["tramite_id"]
    oficina_idx = int(data["oficina_idx"])
    date_from   = data.get("date_from", "")
    date_to     = data.get("date_to", "")
    booking_id  = data.get("booking_id", "TEMP")
    chat_id     = int(data.get("telegram_id", 0))

    oficina_name = PROVINCIA_DATA[province_id]["oficinas"][oficina_idx]

    try:
        result = await _run_playwright(
            province_id=province_id,
            tramite_id=tramite_id,
            oficina_name=oficina_name,
            oficina_idx=oficina_idx,
            data=data,
            date_from=date_from,
            date_to=date_to,
            booking_id=booking_id,
            bot=bot,
            chat_id=chat_id,
            db=db,
        )
        return result
    except Exception as e:
        logger.error(f"book_appointment error: {e}")
        return {"success": False, "error": str(e)}


async def _run_playwright(
    province_id, tramite_id, oficina_name, oficina_idx,
    data, date_from, date_to, booking_id, bot, chat_id, db
) -> dict:

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=HEADLESS,
            args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"]
        )
        ctx = await browser.new_context(
            viewport={"width":1280,"height":900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        try:
            logger.info(f"[{booking_id}] Loading site...")
            await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Accept cookies
            for txt in ["Aceptar","Accept","Acceptar"]:
                btn = page.locator(f"button:has-text('{txt}')").first
                if await btn.count()>0 and await btn.is_visible():
                    await btn.click(); await page.wait_for_timeout(800); break

            # ── Select Province ────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Selecting province {province_id}")
            sel = page.locator("select#provincia, select[name='provincia']").first
            if await sel.count()>0:
                await sel.wait_for(state="visible", timeout=8000)
                await sel.select_option(value=province_id)
                await page.wait_for_timeout(1500)

            # ── Select Tramite ────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Selecting tramite {tramite_id}")
            tsel = page.locator("select#tramite, select[name='tramite']").first
            if await tsel.count()>0:
                await tsel.select_option(value=tramite_id)
                await page.wait_for_timeout(1500)

            # Click Aceptar/Siguiente
            await _click_next(page)

            # ── Check captcha on any step ─────────────────────────────────────
            await _handle_captcha(page, booking_id)

            # ── Select Office ─────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Selecting office: {oficina_name}")
            # Try radio buttons or select for office
            office_radio = page.locator(f"input[type='radio'][value='{oficina_idx}'], input[type='radio']:nth-child({oficina_idx+1})")
            if await office_radio.count()>0:
                await office_radio.first.click()
                await page.wait_for_timeout(1000)
            else:
                # Try select dropdown
                osel = page.locator("select#oficina, select[name='oficina']").first
                if await osel.count()>0:
                    await osel.select_option(index=oficina_idx)
                    await page.wait_for_timeout(1000)

            await _click_next(page)
            await _handle_captcha(page, booking_id)

            # ── Check "no hay citas" ──────────────────────────────────────────
            body = await page.inner_text("body")
            if _no_citas(body):
                return {"success":False, "error":"No hay citas disponibles en este momento"}

            # ── Fill personal data ────────────────────────────────────────────
            logger.info(f"[{booking_id}] Filling personal data")
            await _fill_field(page, ["#txtIdCitado","input[name*='nie']","input[id*='nie']","input[id*='docId']"], data["nie"])
            await _fill_field(page, ["#txtDesCitado","input[name*='nombre']","input[id*='nombre']"], data["nombre"])
            await _fill_field(page, ["input[name*='apellido']","input[id*='apellido']"], data["apellido"])
            await _fill_field(page, ["input[type='email']","input[name*='email']","input[id*='email']"], data["email"])
            await _fill_field(page, ["input[name*='telf']","input[id*='telf']","input[name*='phone']"], data["telefono"])

            # Date of birth
            dob = data["fecha_nac"]  # YYYY-MM-DD from HTML date input
            await _fill_field(page, ["input[name*='fecha']","input[id*='fecha']","input[type='date']"], dob)

            await _click_next(page)
            await _handle_captcha(page, booking_id)

            # ── Handle OTP if required ────────────────────────────────────────
            body = await page.inner_text("body")
            if "código" in body.lower() or "sms" in body.lower() or "otp" in body.lower():
                logger.info(f"[{booking_id}] OTP required")
                otp = ""
                if bot and chat_id and db:
                    otp = await wait_for_otp(bot, chat_id, booking_id, db)
                if otp:
                    await _fill_field(page, ["input[name*='codigo']","input[name*='otp']","input[name*='sms']","input[type='number']"], otp)
                    await _click_next(page)

            # ── Pick appointment slot ─────────────────────────────────────────
            logger.info(f"[{booking_id}] Looking for appointment slots in range {date_from} → {date_to}")
            body = await page.inner_text("body")
            if _no_citas(body):
                return {"success":False, "error":"No hay citas disponibles en este momento"}

            # Find available slots and check date range
            slots = page.locator("a.cita-libre, td.libre a, .cita, input[type='radio']:not([disabled])")
            count = await slots.count()
            slot_clicked = False
            for i in range(count):
                slot = slots.nth(i)
                slot_text = await slot.inner_text() if await slot.count()>0 else ""
                if is_date_in_range(slot_text, date_from, date_to):
                    await slot.click()
                    slot_clicked = True
                    logger.info(f"[{booking_id}] Clicked slot: {slot_text}")
                    await page.wait_for_timeout(1500)
                    break

            if not slot_clicked and count>0:
                # Click first available regardless
                await slots.first.click()
                await page.wait_for_timeout(1500)

            await _click_next(page)
            await _handle_captcha(page, booking_id)
            await page.wait_for_timeout(3000)

            # ── Extract confirmation ──────────────────────────────────────────
            final_body = await page.inner_text("body")
            if _no_citas(final_body):
                return {"success":False, "error":"No hay citas disponibles en el rango de fechas seleccionado"}

            fecha = re.search(r"\d{2}/\d{2}/\d{4}", final_body)
            hora  = re.search(r"\d{2}:\d{2}", final_body)
            loc   = re.search(r"[Ll]ocalizador[:\s]+([A-Z0-9\-]+)", final_body)
            num   = re.search(r"[Nn]úmero[:\s]+([A-Z0-9\-]+)", final_body)

            conf  = (loc.group(1) if loc else "") or (num.group(1) if num else "")
            fecha_str = fecha.group() if fecha else ""
            hora_str  = hora.group()  if hora  else ""

            # ── Save PDF ──────────────────────────────────────────────────────
            pdf_path = ""
            if fecha_str or conf:
                try:
                    pdf_path = await save_confirmation_pdf(page, booking_id)
                except Exception as e:
                    logger.warning(f"PDF save failed: {e}")

            if fecha_str or conf:
                return {
                    "success":      True,
                    "fecha":        fecha_str,
                    "hora":         hora_str,
                    "confirmation": conf,
                    "oficina":      oficina_name,
                    "pdf_path":     pdf_path,
                }
            else:
                # Save debug screenshot
                await page.screenshot(path=f"debug_{booking_id}.png")
                return {"success":False, "error":"No se pudo confirmar la cita. Intenta manualmente."}

        except PWTimeout:
            return {"success":False,"error":"Timeout en la web del gobierno"}
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            return {"success":False,"error":str(e)}
        finally:
            await browser.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _click_next(page):
    for txt in ["Aceptar","Siguiente","Continuar","Enviar","Solicitar","Acceder"]:
        btn = page.locator(f"input[value='{txt}'], button:has-text('{txt}')").first
        if await btn.count()>0 and await btn.is_visible():
            await btn.click()
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(1500)
            return


async def _fill_field(page, selectors: list, value: str):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count()>0 and await el.is_visible():
                await el.fill(str(value))
                return
        except Exception:
            continue


async def _handle_captcha(page, booking_id: str):
    """Detect and solve captcha if present"""
    captcha_img = page.locator("img[src*='captcha'], img[id*='captcha'], img[class*='captcha']").first
    if await captcha_img.count()>0 and await captcha_img.is_visible():
        logger.info(f"[{booking_id}] Captcha detected — solving with 2Captcha")
        img_bytes = await captcha_img.screenshot()
        solution = await solve_captcha_image(img_bytes)
        if solution:
            inp = page.locator("input[name*='captcha'], input[id*='captcha']").first
            if await inp.count()>0:
                await inp.fill(solution)
                await page.wait_for_timeout(500)
                await _click_next(page)


def _no_citas(text: str) -> bool:
    phrases = ["no hay citas","no existen citas","no quedan citas","sin citas disponibles","no available"]
    return any(p in text.lower() for p in phrases)
