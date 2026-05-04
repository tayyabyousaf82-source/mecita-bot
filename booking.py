"""
booking.py v3 — Sin Clave + Con Clave + OTP Telegram notification + PDF upload
"""
import asyncio, logging, base64, httpx, os, re
from datetime import datetime, date
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from config import BOOKING_URL, HEADLESS, CAPTCHA_API_KEY
from data import PROVINCIA_DATA

logger = logging.getLogger(__name__)

# ── 2Captcha ──────────────────────────────────────────────────────────────────

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

# ── PDF ───────────────────────────────────────────────────────────────────────

async def save_confirmation_pdf(page, booking_id: str) -> str:
    os.makedirs("pdfs", exist_ok=True)
    path = f"pdfs/cita_{booking_id}.pdf"
    await page.pdf(path=path, format="A4", print_background=True)
    return path

# ── OTP — Notify + Wait ───────────────────────────────────────────────────────

async def wait_for_otp(bot, chat_id: int, booking_id: str, db, timeout=300) -> str:
    await bot.send_message(
        chat_id,
        f"📱 *¡OTP REQUERIDO!*\n\n"
        f"Se ha enviado un SMS a tu teléfono.\n\n"
        f"Por favor escribe el *código OTP* recibido:\n"
        f"_(Tienes {timeout//60} minutos — solo escribe los números)_",
        parse_mode="Markdown"
    )
    for _ in range(timeout // 3):
        await asyncio.sleep(3)
        otp_row = db.get_pending_otp(booking_id)
        if otp_row:
            db.mark_otp_used(booking_id)
            await bot.send_message(chat_id, "✅ *OTP recibido. Confirmando cita...*", parse_mode="Markdown")
            return otp_row["otp_code"]
    await bot.send_message(chat_id, "⏰ *Tiempo agotado esperando OTP. Se reintentará.*", parse_mode="Markdown")
    return ""

# ── Date Range ────────────────────────────────────────────────────────────────

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

# ── Main Entry ────────────────────────────────────────────────────────────────

async def book_appointment(data: dict, bot=None, db=None) -> dict:
    province_id   = data["province_id"]
    tramite_id    = data["tramite_id"]
    oficina_idx   = data["oficina_idx"]
    date_from     = data.get("date_from", "")
    date_to       = data.get("date_to", "")
    booking_id    = data.get("booking_id", "TEMP")
    chat_id       = int(data.get("telegram_id", 0))
    access_method = data.get("access_method", "sin")

    is_any = str(oficina_idx).upper() == "ANY"
    if is_any:
        oficina_name    = "Cualquier oficina disponible"
        oficina_idx_int = None
    else:
        oficina_idx_int = int(oficina_idx)
        oficina_name    = PROVINCIA_DATA[province_id]["oficinas"][oficina_idx_int]

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
                    result = await _con_clave_login(page, province_id, booking_id, bot, chat_id)
                    if not result["success"]:
                        return result

                result = await _icp_flow(
                    page, province_id, tramite_id, oficina_name, oficina_idx_int,
                    is_any, data, date_from, date_to, booking_id, bot, chat_id, db
                )
                return result
            finally:
                await browser.close()
    except Exception as e:
        logger.error(f"book_appointment error: {e}")
        return {"success": False, "error": str(e)}

# ── CON CLAVE LOGIN ───────────────────────────────────────────────────────────

async def _con_clave_login(page, province_id, booking_id, bot, chat_id) -> dict:
    """Login with digital certificate via Cl@ve"""
    try:
        logger.info(f"[{booking_id}] Con Clave: Starting login")

        # Notify user
        if bot and chat_id:
            await bot.send_message(
                chat_id,
                "🔐 *Iniciando búsqueda Con Cl@ve*\n\n"
                "El bot usará el certificado digital para acceder.\n"
                "_Te notificaré cuando llegue al OTP..._",
                parse_mode="Markdown"
            )

        await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Accept cookies
        for txt in ["Aceptar", "Accept"]:
            btn = page.locator(f"button:has-text('{txt}')").first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(800)
                break

        # Click Cl@ve / Certificate button
        clave_selectors = [
            "a:has-text('Cl@ve')", "button:has-text('Cl@ve')",
            "a:has-text('Clave')", "a:has-text('certificado')",
            "#btnClave", ".btn-clave", "input[value*='Clave']",
        ]
        clicked = False
        for sel in clave_selectors:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(2000)
                clicked = True
                logger.info(f"[{booking_id}] Clave button clicked: {sel}")
                break

        if not clicked:
            logger.warning(f"[{booking_id}] No Clave button found, continuing normally")

        return {"success": True}
    except Exception as e:
        logger.error(f"Con Clave login error: {e}")
        return {"success": False, "error": f"Con Clave login failed: {e}"}

# ── ICP FLOW ──────────────────────────────────────────────────────────────────

async def _icp_flow(
    page, province_id, tramite_id, oficina_name, oficina_idx,
    is_any, data, date_from, date_to, booking_id, bot, chat_id, db
) -> dict:

    try:
        # Load page (if not already loaded by Con Clave)
        current_url = page.url
        if "icp" not in current_url.lower():
            await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            for txt in ["Aceptar", "Accept"]:
                btn = page.locator(f"button:has-text('{txt}')").first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(800)
                    break

        # Province
        psel = page.locator("select#provincia, select[name='provincia']").first
        if await psel.count() > 0:
            await psel.wait_for(state="visible", timeout=8000)
            await psel.select_option(value=province_id)
            await page.wait_for_timeout(1500)

        # Tramite
        tsel = page.locator("select#tramite, select[name='tramite']").first
        if await tsel.count() > 0:
            await tsel.select_option(value=tramite_id)
            await page.wait_for_timeout(1500)

        await _click_next(page)
        await _handle_captcha(page, booking_id)

        # Office
        if is_any:
            selected_office = await _auto_select_office(page, booking_id)
            if not selected_office:
                return {"success": False, "error": "No se pudo seleccionar ninguna oficina"}
        else:
            await _select_specific_office(page, oficina_idx, oficina_name, booking_id)

        await _click_next(page)
        await _handle_captcha(page, booking_id)

        body = await page.inner_text("body")
        if _no_citas(body):
            return {"success": False, "error": "No hay citas disponibles"}

        # Personal Data
        doc_type = data.get("doc_type", "NIE")
        # Select doc type if radio present
        for sel in [
            f"input[type='radio'][value='{doc_type}']",
            f"select#tipoDocumento option[value='{doc_type}']",
        ]:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.click()
                await page.wait_for_timeout(300)
                break

        await _fill_field(page,
            ["#txtIdCitado", "input[name*='nie']", "input[id*='nie']", "input[id*='docId']"],
            data["nie"])
        await _fill_field(page,
            ["#txtDesCitado", "input[name*='nombre']", "input[id*='nombre']"],
            data["nombre"])
        await _fill_field(page,
            ["input[type='email']", "input[name*='email']", "input[id*='email']"],
            data["email"])
        await _fill_field(page,
            ["input[name*='telf']", "input[id*='telf']", "input[name*='phone']"],
            data["telefono"])
        await _fill_field(page,
            ["input[name*='fecha']", "input[id*='fecha']", "input[type='date']"],
            data.get("fecha_nac", ""))

        await _click_next(page)
        await _handle_captcha(page, booking_id)

        # OTP Detection — Notify user
        body = await page.inner_text("body")
        if any(w in body.lower() for w in ["código", "sms", "otp", "verificacion", "codigo"]):
            logger.info(f"[{booking_id}] OTP page — notifying user")
            if bot and chat_id:
                try:
                    screenshot = await page.screenshot()
                    await bot.send_photo(
                        chat_id, photo=screenshot,
                        caption=(
                            "📱 *OTP REQUERIDO*\n\n"
                            "El bot llegó a la página de verificación SMS.\n"
                            "Por favor envía el código que recibiste."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
                if db:
                    otp = await wait_for_otp(bot, chat_id, booking_id, db)
                    if otp:
                        await _fill_field(page,
                            ["input[name*='codigo']", "input[name*='otp']",
                             "input[name*='sms']", "input[maxlength='6']",
                             "input[maxlength='4']", "input[type='number']"], otp)
                        await _click_next(page)
                        await page.wait_for_timeout(2000)

        # Slot Selection
        body = await page.inner_text("body")
        if _no_citas(body):
            return {"success": False, "error": "No hay citas disponibles"}

        slots = page.locator(
            "a.cita-libre, td.libre a, .cita, "
            "input[type='radio']:not([disabled]), "
            "td[class*='libre'], a[class*='cita']"
        )
        slot_count = await slots.count()
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
                await page.wait_for_timeout(1500)
                break

        if not slot_clicked and slot_count > 0:
            await slots.first.click()
            await page.wait_for_timeout(1500)

        await _click_next(page)
        await _handle_captcha(page, booking_id)
        await page.wait_for_timeout(3000)

        # Confirmation
        final_body = await page.inner_text("body")
        if _no_citas(final_body):
            return {"success": False, "error": "No hay citas en el rango"}

        fecha = re.search(r"\d{2}/\d{2}/\d{4}", final_body)
        hora  = re.search(r"\d{2}:\d{2}", final_body)
        loc   = re.search(r"[Ll]ocalizador[:\s]+([A-Z0-9\-]+)", final_body)
        num   = re.search(r"[Nn]úmero[:\s]+([A-Z0-9\-]+)", final_body)

        conf      = (loc.group(1) if loc else "") or (num.group(1) if num else "")
        fecha_str = fecha.group() if fecha else ""
        hora_str  = hora.group()  if hora  else ""

        pdf_path = ""
        if fecha_str or conf:
            try:
                pdf_path = await save_confirmation_pdf(page, booking_id)
            except Exception as e:
                logger.warning(f"PDF error: {e}")

        if fecha_str or conf:
            return {
                "success": True, "fecha": fecha_str, "hora": hora_str,
                "confirmation": conf, "oficina": oficina_name, "pdf_path": pdf_path,
            }
        else:
            await page.screenshot(path=f"debug_{booking_id}.png")
            return {"success": False, "error": "No se pudo confirmar la cita"}

    except PWTimeout:
        return {"success": False, "error": "Timeout en la web del gobierno"}
    except Exception as e:
        logger.error(f"ICP flow error [{booking_id}]: {e}")
        return {"success": False, "error": str(e)}

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _auto_select_office(page, booking_id: str) -> str:
    await page.wait_for_timeout(1500)
    selects = page.locator("select#oficina, select[name='oficina'], select[id*='ofic']")
    if await selects.count() > 0:
        sel = selects.first
        if await sel.is_visible():
            options = await sel.locator("option").all()
            for opt in options:
                val = await opt.get_attribute("value")
                txt = await opt.inner_text()
                if val and val not in ["", "0", "-1"] and txt.strip() and "selecciona" not in txt.lower():
                    await sel.select_option(value=val)
                    await page.wait_for_timeout(1000)
                    return txt.strip()
    radios = page.locator("input[type='radio']")
    if await radios.count() > 0:
        await radios.first.click()
        await page.wait_for_timeout(1000)
        return "Oficina seleccionada"
    return ""

async def _select_specific_office(page, oficina_idx: int, oficina_name: str, booking_id: str):
    await page.wait_for_timeout(1000)
    sel = page.locator("select#oficina, select[name='oficina'], select[id*='ofic']").first
    if await sel.count() > 0 and await sel.is_visible():
        try:
            await sel.select_option(index=oficina_idx)
            await page.wait_for_timeout(1000)
            return
        except Exception:
            pass
    radios = page.locator("input[type='radio']")
    if await radios.count() > oficina_idx:
        await radios.nth(oficina_idx).click()
        await page.wait_for_timeout(1000)

async def _click_next(page):
    for txt in ["Aceptar", "Siguiente", "Continuar", "Enviar", "Solicitar", "Acceder"]:
        btn = page.locator(f"input[value='{txt}'], button:has-text('{txt}')").first
        if await btn.count() > 0 and await btn.is_visible():
            await btn.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(1500)
            return

async def _fill_field(page, selectors: list, value: str):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible():
                await el.fill(str(value))
                return
        except Exception:
            continue

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
                await page.wait_for_timeout(500)
                await _click_next(page)

def _no_citas(text: str) -> bool:
    phrases = ["no hay citas", "no existen citas", "no quedan citas", "sin citas disponibles"]
    return any(p in text.lower() for p in phrases)
