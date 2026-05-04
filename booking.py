"""
booking.py v5
─────────────────────────────────────────────────────────────────────────────
Refresh logic  (ONLY for "No hay cita disponible" page):
  • Bot us page par 10 sec wait karta hai
  • Jaise hi clock second == 31 hota hai → page reload (F5 jaise)
  • Reload = sirf us page ko refresh, pura flow dobara nahi
  • Agar office available ho → immediately select + Siguiente click

OTP logic:
  • OTP maango Telegram se
  • Galat ho → bar bar maango jab tak sahi na ho (koi limit nahi)
  • Sahi OTP → confirm → PDF + full details user + admin dono ko

Office priority:
  • User ne jo specific office select ki → pehle wahi try karo
  • "ANY" mode → koi bhi jo available ho → immediately select
─────────────────────────────────────────────────────────────────────────────
"""
import asyncio, logging, base64, httpx, os, re, time
from datetime import datetime, date
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from config import BOOKING_URL, HEADLESS, CAPTCHA_API_KEY, ADMIN_IDS
from data import PROVINCIA_DATA

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
#  2Captcha
# ═══════════════════════════════════════════════════════════════════════════════

async def solve_captcha_image(img_bytes: bytes) -> str:
    if not CAPTCHA_API_KEY:
        return ""
    b64 = base64.b64encode(img_bytes).decode()
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post("https://2captcha.com/in.php", data={
            "key": CAPTCHA_API_KEY, "method": "base64", "body": b64, "json": 1,
        })
        data = r.json()
        if data.get("status") != 1:
            return ""
        captcha_id = data["request"]
        for _ in range(24):
            await asyncio.sleep(5)
            res = await client.get("https://2captcha.com/res.php", params={
                "key": CAPTCHA_API_KEY, "action": "get", "id": captcha_id, "json": 1,
            })
            rd = res.json()
            if rd.get("status") == 1:
                return rd["request"]
            if rd.get("request") != "CAPCHA_NOT_READY":
                return ""
    return ""

# ═══════════════════════════════════════════════════════════════════════════════
#  PDF save
# ═══════════════════════════════════════════════════════════════════════════════

async def save_confirmation_pdf(page, booking_id: str) -> str:
    os.makedirs("pdfs", exist_ok=True)
    path = f"pdfs/cita_{booking_id}.pdf"
    await page.pdf(path=path, format="A4", print_background=True)
    return path

# ═══════════════════════════════════════════════════════════════════════════════
#  OTP — bar bar maango jab tak sahi na ho
# ═══════════════════════════════════════════════════════════════════════════════

async def wait_for_otp(bot, chat_id: int, booking_id: str, db,
                       attempt_num: int = 1, timeout: int = 300) -> str:
    """
    Telegram par OTP maango. Galat hua to dobara call hoga.
    attempt_num: pehli baar = 1, dobara = 2, 3 ...
    """
    if attempt_num == 1:
        msg = (
            "📱 *OTP Code Required!*\n\n"
            "Aapke phone par SMS aaya hai.\n\n"
            "Sirf numbers likho (4-8 digits):\n"
            f"_({timeout//60} minute mein bhejein)_"
        )
    else:
        msg = (
            f"❌ *OTP Galat Tha! (Attempt #{attempt_num})*\n\n"
            "Sahi OTP code bhejein:\n"
            "_(Check karo SMS phir se)_"
        )

    await bot.send_message(chat_id, msg, parse_mode="Markdown")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        await asyncio.sleep(3)
        otp_row = db.get_pending_otp(booking_id)
        if otp_row:
            db.mark_otp_used(booking_id)
            return otp_row["otp_code"]

    await bot.send_message(
        chat_id,
        "⏰ *OTP timeout.* Bot phir try karega.",
        parse_mode="Markdown"
    )
    return ""

# ═══════════════════════════════════════════════════════════════════════════════
#  Confirmation message — user + admin
# ═══════════════════════════════════════════════════════════════════════════════

async def send_confirmation(bot, chat_id: int, result: dict, data: dict, pdf_path: str):
    """
    Full details user ko aur har admin ko bhejo:
    fecha, hora, oficina, tramite, justification/localizador, pdf
    """
    msg = (
        "🎉 *¡CITA CONFIRMADA!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 *Fecha:* `{result.get('fecha','')}`\n"
        f"🕐 *Hora:* `{result.get('hora','')}`\n"
        f"🏢 *Oficina:* {result.get('oficina','')}\n"
        f"📋 *Trámite:* {data.get('tramite_name','')}\n"
        f"📍 *Provincia:* {data.get('province_name','')}\n"
        f"🔖 *Localizador:* `{result.get('confirmation','')}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📄 Justificante adjunto."
    )

    # User ko bhejo
    await bot.send_message(chat_id, msg, parse_mode="Markdown")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            await bot.send_document(
                chat_id, f,
                filename=f"cita_{result.get('confirmation','confirmacion')}.pdf",
                caption="📄 Justificante de cita"
            )

    # Har admin ko bhejo
    for admin_id in ADMIN_IDS:
        if admin_id and admin_id != chat_id:
            try:
                admin_msg = (
                    "🔔 *NUEVA CITA CONFIRMADA*\n"
                    f"👤 User ID: `{chat_id}`\n"
                    f"📛 Nombre: {data.get('nombre','')}\n"
                    f"🪪 NIE: `{data.get('nie','')}`\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📅 *Fecha:* `{result.get('fecha','')}`\n"
                    f"🕐 *Hora:* `{result.get('hora','')}`\n"
                    f"🏢 *Oficina:* {result.get('oficina','')}\n"
                    f"📋 *Trámite:* {data.get('tramite_name','')}\n"
                    f"📍 *Provincia:* {data.get('province_name','')}\n"
                    f"🔖 *Localizador:* `{result.get('confirmation','')}`"
                )
                await bot.send_message(admin_id, admin_msg, parse_mode="Markdown")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        await bot.send_document(
                            admin_id, f,
                            filename=f"cita_{result.get('confirmation','confirmacion')}.pdf",
                            caption=f"📄 Justificante — User {chat_id}"
                        )
            except Exception as e:
                logger.warning(f"Admin {admin_id} notify failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _no_citas(text: str) -> bool:
    phrases = ["no hay citas", "no existen citas", "no quedan citas", "sin citas disponibles"]
    return any(p in text.lower() for p in phrases)

def is_date_in_range(date_str: str, date_from: str, date_to: str) -> bool:
    if not date_str or not date_from or not date_to:
        return True
    try:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", date_str)
        if not m:
            return True
        d, mo, y = m.groups()
        slot_date = date(int(y), int(mo), int(d))
        return date.fromisoformat(date_from) <= slot_date <= date.fromisoformat(date_to)
    except Exception:
        return True

async def _accept_cookies(page):
    for txt in ["Aceptar", "Accept"]:
        btn = page.locator(f"button:has-text('{txt}')").first
        if await btn.count() > 0 and await btn.is_visible():
            await btn.click()
            await page.wait_for_timeout(800)
            break

async def _click_btn(page, labels):
    """Click first visible button matching any label."""
    for txt in labels:
        btn = page.locator(f"input[value='{txt}'], button:has-text('{txt}')").first
        if await btn.count() > 0 and await btn.is_visible():
            await btn.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(1000)
            return True
    return False

async def _fill_field(page, selectors: list, value: str):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible():
                await el.fill(str(value))
                return
        except Exception:
            continue

async def _auto_click_checkboxes(page, booking_id: str):
    """All unchecked visible checkboxes click karo (terms, privacy, etc)."""
    checkboxes = page.locator("input[type='checkbox']")
    count = await checkboxes.count()
    for i in range(count):
        cb = checkboxes.nth(i)
        try:
            if await cb.is_visible() and not await cb.is_checked():
                await cb.click()
                await page.wait_for_timeout(150)
                logger.info(f"[{booking_id}] Checkbox {i+1}/{count} clicked")
        except Exception:
            pass

async def _handle_captcha(page, booking_id: str):
    captcha_img = page.locator(
        "img[src*='captcha'], img[id*='captcha'], img[class*='captcha']"
    ).first
    if await captcha_img.count() > 0 and await captcha_img.is_visible():
        img_bytes = await captcha_img.screenshot()
        solution  = await solve_captcha_image(img_bytes)
        if solution:
            inp = page.locator("input[name*='captcha'], input[id*='captcha']").first
            if await inp.count() > 0:
                await inp.fill(solution)
                await page.wait_for_timeout(400)
                await _click_btn(page, ["Aceptar", "Siguiente", "Continuar", "Enviar"])

# ═══════════════════════════════════════════════════════════════════════════════
#  "No hay cita" page — wait 10s then reload at second==31
# ═══════════════════════════════════════════════════════════════════════════════

async def wait_and_reload_no_cita(page, booking_id: str, interval_idx: int) -> int:
    """
    "No hay cita disponible" page par:
      1. 10 sec wait
      2. Jaise hi second == 31 ho → page.reload()
      3. Returns updated interval_idx for next long wait cycle

    Long wait intervals (1, 3, 5, 7 min) sirf tab use hote hain
    jab 31-sec window miss ho jaye (edge case).
    """
    LONG_INTERVALS = [60, 180, 300, 420]  # 1, 3, 5, 7 min

    # ── Step 1: 10 sec wait ───────────────────────────────────────────────────
    logger.info(f"[{booking_id}] No cita — waiting 10s before checking second=31")
    await asyncio.sleep(10)

    # ── Step 2: Wait until second hits 31 ─────────────────────────────────────
    logger.info(f"[{booking_id}] Waiting for second=31 to reload...")
    waited_extra = 0
    while True:
        now_sec = datetime.now().second
        if now_sec == 31:
            break
        await asyncio.sleep(0.5)
        waited_extra += 0.5
        # Safety: agar 60+ sec wait ho jaye to bina 31 ke bhi reload karo
        if waited_extra >= 60:
            logger.info(f"[{booking_id}] 60s passed waiting for sec=31, reloading anyway")
            break

    # ── Step 3: Reload page ────────────────────────────────────────────────────
    logger.info(f"[{booking_id}] 🔄 Reloading 'no cita' page (sec={datetime.now().second})")
    try:
        await page.reload(wait_until="networkidle", timeout=20000)
    except Exception:
        try:
            await page.reload(timeout=15000)
        except Exception as e:
            logger.warning(f"[{booking_id}] Reload failed: {e}")

    await page.wait_for_timeout(1500)

    # Cycle next long interval (for logging only, not used for waiting here)
    next_idx = (interval_idx + 1) % len(LONG_INTERVALS)
    return next_idx

# ═══════════════════════════════════════════════════════════════════════════════
#  Main Entry
# ═══════════════════════════════════════════════════════════════════════════════

async def book_appointment(data: dict, bot=None, db=None, booking_id=None) -> dict:
    province_id   = data["province_id"]
    tramite_id    = data["tramite_id"]
    oficina_idx   = data["oficina_idx"]
    date_from     = data.get("date_from", "")
    date_to       = data.get("date_to", "")
    if not booking_id:
        booking_id = data.get("booking_id", "TEMP")
    chat_id       = int(data.get("telegram_id", 0))
    access_method = data.get("access_method", "sin")

    is_any = str(oficina_idx).upper() == "ANY"
    preferred_idx  = None if is_any else int(oficina_idx)
    preferred_name = None if is_any else PROVINCIA_DATA[province_id]["oficinas"][preferred_idx]

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=HEADLESS,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await ctx.new_page()
            try:
                if access_method == "con":
                    res = await _con_clave_login(page, booking_id, bot, chat_id)
                    if not res["success"]:
                        return res

                return await _full_flow(
                    page, province_id, tramite_id,
                    preferred_name, preferred_idx, is_any,
                    data, date_from, date_to,
                    booking_id, bot, chat_id, db
                )
            finally:
                await browser.close()
    except Exception as e:
        logger.error(f"[{booking_id}] book_appointment exception: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
#  Con Clave login
# ═══════════════════════════════════════════════════════════════════════════════

async def _con_clave_login(page, booking_id, bot, chat_id) -> dict:
    try:
        if bot and chat_id:
            await bot.send_message(
                chat_id,
                "🔐 *Con Cl@ve login shuru...*",
                parse_mode="Markdown"
            )
        await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        await _accept_cookies(page)
        for sel in ["a:has-text('Cl@ve')", "button:has-text('Cl@ve')",
                    "a:has-text('Clave')", "#btnClave", ".btn-clave"]:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(2000)
                break
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": f"Con Clave failed: {e}"}

# ═══════════════════════════════════════════════════════════════════════════════
#  Full booking flow with inline "no cita" reload loop
# ═══════════════════════════════════════════════════════════════════════════════

async def _full_flow(
    page, province_id, tramite_id,
    preferred_name, preferred_idx, is_any,
    data, date_from, date_to,
    booking_id, bot, chat_id, db
) -> dict:

    interval_idx = 0  # for long-wait cycling tracking

    try:
        # ── Load page ─────────────────────────────────────────────────────────
        if "icp" not in page.url.lower():
            await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            await _accept_cookies(page)

        # ── Province ──────────────────────────────────────────────────────────
        psel = page.locator("select#provincia, select[name='provincia']").first
        if await psel.count() > 0:
            await psel.wait_for(state="visible", timeout=8000)
            await psel.select_option(value=province_id)
            await page.wait_for_timeout(1200)

        # ── Tramite ───────────────────────────────────────────────────────────
        tsel = page.locator("select#tramite, select[name='tramite']").first
        if await tsel.count() > 0:
            await tsel.select_option(value=tramite_id)
            await page.wait_for_timeout(1200)

        await _click_btn(page, ["Aceptar", "Siguiente", "Continuar", "Enviar", "Solicitar", "Acceder"])
        await _handle_captcha(page, booking_id)

        # ════════════════════════════════════════════════════════════════════════
        #  OFFICE SELECTION LOOP
        #  "No cita disponible" → reload at sec=31 → check again → loop
        # ════════════════════════════════════════════════════════════════════════
        selected_office = None

        while True:
            body = await page.inner_text("body")

            # ── Agar "no cita" page hai → reload loop ─────────────────────────
            if _no_citas(body):
                logger.info(f"[{booking_id}] No cita on office page — waiting 10s then reload at sec=31")
                interval_idx = await wait_and_reload_no_cita(page, booking_id, interval_idx)
                # Reload ke baad body check karo dobara
                try:
                    body = await page.inner_text("body")
                except Exception:
                    break
                if _no_citas(body):
                    continue  # still no cita — loop again
                # Cita aa gayi — neeche select karo
            
            # ── Office select karo ─────────────────────────────────────────────
            # Priority 1: Preferred specific office
            if not is_any and preferred_idx is not None:
                sel_ok = await _select_office_by_idx(page, preferred_idx, preferred_name, booking_id)
                if sel_ok:
                    selected_office = preferred_name
                    logger.info(f"[{booking_id}] ✓ Preferred office selected: {preferred_name}")
                    # Immediately Siguiente!
                    await _click_btn(page, ["Siguiente", "Aceptar", "Continuar"])
                    break

            # Priority 2: Any available office
            office_name = await _select_any_available_office(page, booking_id)
            if office_name:
                selected_office = office_name
                logger.info(f"[{booking_id}] ✓ Office selected: {office_name}")
                # Immediately Siguiente!
                await _click_btn(page, ["Siguiente", "Aceptar", "Continuar"])
                break

            # Koi office nahi mili → reload dobara
            logger.info(f"[{booking_id}] No office available yet — reload loop")
            interval_idx = await wait_and_reload_no_cita(page, booking_id, interval_idx)

        if not selected_office:
            return {"success": False, "error": "No hay citas disponibles"}

        await _handle_captcha(page, booking_id)

        # ── Post-office "no cita" check ───────────────────────────────────────
        body = await page.inner_text("body")
        if _no_citas(body):
            return {"success": False, "error": "No hay citas disponibles"}

        # ── Personal Data ─────────────────────────────────────────────────────
        doc_type = data.get("doc_type", "NIE")
        for sel in [f"input[type='radio'][value='{doc_type}']"]:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.click()
                await page.wait_for_timeout(200)
                break

        await _fill_field(page, ["#txtIdCitado","input[name*='nie']","input[id*='nie']","input[id*='docId']"], data["nie"])
        await _fill_field(page, ["#txtDesCitado","input[name*='nombre']","input[id*='nombre']"], data["nombre"])
        await _fill_field(page, ["input[type='email']","input[name*='email']","input[id*='email']"], data["email"])
        await _fill_field(page, ["input[name*='telf']","input[id*='telf']","input[name*='phone']"], data["telefono"])
        await _fill_field(page, ["input[name*='fecha']","input[id*='fecha']","input[type='date']"], data.get("fecha_nac",""))

        await _auto_click_checkboxes(page, booking_id)
        await _click_btn(page, ["Aceptar", "Siguiente", "Continuar", "Enviar", "Solicitar"])
        await _handle_captcha(page, booking_id)

        # ════════════════════════════════════════════════════════════════════════
        #  OTP — bar bar maango jab tak sahi na ho
        # ════════════════════════════════════════════════════════════════════════
        body = await page.inner_text("body")
        if any(w in body.lower() for w in ["código", "sms", "otp", "verificacion", "codigo"]):
            logger.info(f"[{booking_id}] OTP page detected")
            await _auto_click_checkboxes(page, booking_id)

            if bot and chat_id:
                # Screenshot bhejo
                try:
                    screenshot = await page.screenshot()
                    await bot.send_photo(
                        chat_id, photo=screenshot,
                        caption="📱 *OTP page — Code bhejein*",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

            if db:
                otp_attempt = 1
                while True:
                    # OTP maango
                    otp = await wait_for_otp(
                        bot, chat_id, booking_id, db,
                        attempt_num=otp_attempt
                    )
                    if not otp:
                        # Timeout — phir maango
                        otp_attempt += 1
                        continue

                    # OTP fill karo
                    await _fill_field(page,
                        ["input[name*='codigo']","input[name*='otp']",
                         "input[name*='sms']","input[maxlength='6']",
                         "input[maxlength='4']","input[type='number']"], otp)

                    await _auto_click_checkboxes(page, booking_id)
                    await _click_btn(page, ["Aceptar", "Siguiente", "Continuar", "Enviar"])
                    await page.wait_for_timeout(2000)

                    body = await page.inner_text("body")
                    otp_error_phrases = [
                        "código incorrecto", "otp incorrecto", "código erróneo",
                        "invalid code", "código no válido", "incorrecto", "wrong code",
                        "no válido"
                    ]
                    is_wrong = any(p in body.lower() for p in otp_error_phrases)

                    if not is_wrong:
                        logger.info(f"[{booking_id}] ✓ OTP accepted (attempt {otp_attempt})")
                        break  # OTP sahi laga — aage baro

                    # Galat OTP — dobara maango
                    logger.warning(f"[{booking_id}] OTP wrong (attempt {otp_attempt})")
                    otp_attempt += 1
                    # (loop continues — next wait_for_otp will show "galat" message)

        # ── Slot Selection ────────────────────────────────────────────────────
        body = await page.inner_text("body")
        if _no_citas(body):
            return {"success": False, "error": "No hay citas disponibles"}

        slots = page.locator(
            "a.cita-libre, td.libre a, .cita, "
            "input[type='radio']:not([disabled]), "
            "td[class*='libre'], a[class*='cita']"
        )
        slot_count  = await slots.count()
        slot_clicked = False

        for i in range(slot_count):
            slot = slots.nth(i)
            try:
                slot_text = await slot.inner_text()
            except Exception:
                slot_text = ""
            if is_date_in_range(slot_text, date_from, date_to):
                await slot.click()
                slot_clicked = True
                await page.wait_for_timeout(1200)
                break

        if not slot_clicked and slot_count > 0:
            await slots.first.click()
            await page.wait_for_timeout(1200)

        await _click_btn(page, ["Aceptar", "Siguiente", "Continuar", "Enviar", "Solicitar"])
        await _handle_captcha(page, booking_id)
        await page.wait_for_timeout(3000)

        # ── Confirmation page parse ───────────────────────────────────────────
        final_body = await page.inner_text("body")
        if _no_citas(final_body):
            return {"success": False, "error": "No hay citas en el rango"}

        fecha = re.search(r"\d{2}/\d{2}/\d{4}", final_body)
        hora  = re.search(r"\d{2}:\d{2}", final_body)
        loc   = re.search(r"[Ll]ocalizador[:\s]+([A-Z0-9\-]+)", final_body)
        num   = re.search(r"[Nn]úmero[:\s]+([A-Z0-9\-]+)", final_body)
        just  = re.search(r"[Jj]ustificante[:\s]+([A-Z0-9\-]+)", final_body)

        conf      = (loc.group(1) if loc else "") or (num.group(1) if num else "") or (just.group(1) if just else "")
        fecha_str = fecha.group() if fecha else ""
        hora_str  = hora.group()  if hora  else ""

        pdf_path = ""
        try:
            pdf_path = await save_confirmation_pdf(page, booking_id)
        except Exception as e:
            logger.warning(f"[{booking_id}] PDF error: {e}")

        if fecha_str or conf:
            result = {
                "success": True,
                "fecha":        fecha_str,
                "hora":         hora_str,
                "confirmation": conf,
                "oficina":      selected_office,
                "pdf_path":     pdf_path,
            }
            # Send full confirmation to user + admins
            if bot and chat_id:
                await send_confirmation(bot, chat_id, result, data, pdf_path)
            return result
        else:
            await page.screenshot(path=f"debug_{booking_id}.png")
            return {"success": False, "error": "Confirmation page not detected"}

    except PWTimeout:
        return {"success": False, "error": "Timeout en la web del gobierno"}
    except Exception as e:
        logger.error(f"[{booking_id}] _full_flow error: {e}")
        return {"success": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
#  Office selection helpers
# ═══════════════════════════════════════════════════════════════════════════════

async def _select_office_by_idx(page, oficina_idx: int, oficina_name: str,
                                 booking_id: str) -> bool:
    """Specific index se office select karo. True agar mili."""
    await page.wait_for_timeout(800)
    sel = page.locator("select#oficina, select[name='oficina'], select[id*='ofic']").first
    if await sel.count() > 0 and await sel.is_visible():
        try:
            await sel.select_option(index=oficina_idx)
            await page.wait_for_timeout(800)
            return True
        except Exception:
            # Name se try karo
            try:
                options = await sel.locator("option").all()
                for opt in options:
                    txt = await opt.inner_text()
                    if oficina_name and oficina_name.lower() in txt.lower():
                        val = await opt.get_attribute("value")
                        await sel.select_option(value=val)
                        await page.wait_for_timeout(800)
                        return True
            except Exception:
                pass

    radios = page.locator("input[type='radio']")
    if await radios.count() > oficina_idx:
        await radios.nth(oficina_idx).click()
        await page.wait_for_timeout(800)
        return True

    return False


async def _select_any_available_office(page, booking_id: str) -> str:
    """Koi bhi available office select karo. Office name return karo ya ''."""
    await page.wait_for_timeout(800)
    sel_el = page.locator("select#oficina, select[name='oficina'], select[id*='ofic']").first

    if await sel_el.count() > 0 and await sel_el.is_visible():
        options = await sel_el.locator("option").all()
        for opt in options:
            val = await opt.get_attribute("value")
            txt = (await opt.inner_text()).strip()
            if val and val not in ["", "0", "-1"] and txt and "selecciona" not in txt.lower():
                await sel_el.select_option(value=val)
                await page.wait_for_timeout(800)
                return txt

    radios = page.locator("input[type='radio']")
    if await radios.count() > 0:
        await radios.first.click()
        await page.wait_for_timeout(800)
        return "Oficina seleccionada"

    return ""
