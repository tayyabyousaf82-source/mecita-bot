"""
booking.py — Full auto-booking engine v2
Features:
  - 2Captcha integration (base64 image solve)
  - OTP handling
  - PDF download of confirmation
  - 24/7 retry with date range filtering
  - ANY office: auto-select first available on website
"""
import asyncio, logging, base64, httpx, os, re
from datetime import datetime, date
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from config import BOOKING_URL, HEADLESS, CAPTCHA_API_KEY, SPANISH_PHONE
from data import PROVINCIA_DATA

logger = logging.getLogger(__name__)

# ─── 2Captcha ─────────────────────────────────────────────────────────────────

async def solve_captcha_image(img_bytes: bytes) -> str:
    if not CAPTCHA_API_KEY:
        logger.warning("No 2Captcha API key set")
        return ""
    b64 = base64.b64encode(img_bytes).decode()
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post("https://2captcha.com/in.php", data={
            "key": CAPTCHA_API_KEY, "method": "base64", "body": b64, "json": 1,
        })
        data = r.json()
        if data.get("status") != 1:
            logger.error(f"2Captcha submit error: {data}")
            return ""
        captcha_id = data["request"]
        logger.info(f"2Captcha ID: {captcha_id} — waiting...")
        for _ in range(24):
            await asyncio.sleep(5)
            res = await client.get("https://2captcha.com/res.php", params={
                "key": CAPTCHA_API_KEY, "action": "get", "id": captcha_id, "json": 1,
            })
            rd = res.json()
            if rd.get("status") == 1:
                logger.info(f"2Captcha solved: {rd['request']}")
                return rd["request"]
            if rd.get("request") != "CAPCHA_NOT_READY":
                logger.error(f"2Captcha error: {rd}")
                return ""
    return ""

# ─── PDF ──────────────────────────────────────────────────────────────────────

async def save_confirmation_pdf(page, booking_id: str) -> str:
    os.makedirs("pdfs", exist_ok=True)
    path = f"pdfs/cita_{booking_id}.pdf"
    await page.pdf(path=path, format="A4", print_background=True)
    logger.info(f"PDF saved: {path}")
    return path

# ─── OTP ──────────────────────────────────────────────────────────────────────

async def wait_for_otp(bot, chat_id: int, booking_id: str, db, timeout=120) -> str:
    await bot.send_message(
        chat_id,
        f"📱 *Se ha enviado un SMS a tu teléfono.*\n\n"
        f"Por favor escribe el *código OTP* que has recibido:\n_(Tienes {timeout//60} minutos)_",
        parse_mode="Markdown")
    for _ in range(timeout // 3):
        await asyncio.sleep(3)
        otp_row = db.get_pending_otp(booking_id)
        if otp_row:
            db.mark_otp_used(booking_id)
            return otp_row["otp_code"]
    return ""

# ─── Date Range Check ─────────────────────────────────────────────────────────

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

# ─── Main Entry ───────────────────────────────────────────────────────────────

async def book_appointment(data: dict, bot=None, db=None) -> dict:
    province_id = data["province_id"]
    tramite_id  = data["tramite_id"]
    oficina_idx = data["oficina_idx"]   # "ANY" or number string
    date_from   = data.get("date_from", "")
    date_to     = data.get("date_to", "")
    booking_id  = data.get("booking_id", "TEMP")
    chat_id     = int(data.get("telegram_id", 0))

    is_any = str(oficina_idx).upper() == "ANY"

    if is_any:
        oficina_name    = "Cualquier oficina disponible"
        oficina_idx_int = None
    else:
        oficina_idx_int = int(oficina_idx)
        oficina_name    = PROVINCIA_DATA[province_id]["oficinas"][oficina_idx_int]

    try:
        result = await _run_playwright(
            province_id=province_id,
            tramite_id=tramite_id,
            oficina_name=oficina_name,
            oficina_idx=oficina_idx_int,   # None = ANY
            is_any=is_any,
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

# ─── Playwright Core ──────────────────────────────────────────────────────────

async def _run_playwright(
    province_id, tramite_id, oficina_name, oficina_idx,
    is_any, data, date_from, date_to, booking_id, bot, chat_id, db
) -> dict:

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=HEADLESS,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await ctx.new_page()

        try:
            # ── Load page ─────────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Loading {BOOKING_URL}")
            await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # Accept cookies
            for txt in ["Aceptar", "Accept", "Acceptar"]:
                btn = page.locator(f"button:has-text('{txt}')").first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(800)
                    break

            # ── Province ──────────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Province: {province_id}")
            psel = page.locator("select#provincia, select[name='provincia']").first
            if await psel.count() > 0:
                await psel.wait_for(state="visible", timeout=8000)
                await psel.select_option(value=province_id)
                await page.wait_for_timeout(1500)

            # ── Tramite ───────────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Tramite: {tramite_id}")
            tsel = page.locator("select#tramite, select[name='tramite']").first
            if await tsel.count() > 0:
                await tsel.select_option(value=tramite_id)
                await page.wait_for_timeout(1500)

            await _click_next(page)
            await _handle_captcha(page, booking_id)

            # ── Office Selection ──────────────────────────────────────────────
            if is_any:
                # AUTO MODE: website pe jo bhi pehli office available ho select karo
                logger.info(f"[{booking_id}] ANY office mode — auto selecting on website")
                selected_office = await _auto_select_office(page, booking_id)
                if not selected_office:
                    return {"success": False, "error": "No se pudo seleccionar ninguna oficina en el sitio web"}
                logger.info(f"[{booking_id}] Website auto-selected: {selected_office}")
            else:
                # SPECIFIC OFFICE
                logger.info(f"[{booking_id}] Specific office idx={oficina_idx}: {oficina_name}")
                await _select_specific_office(page, oficina_idx, oficina_name, booking_id)

            await _click_next(page)
            await _handle_captcha(page, booking_id)

            # ── Check no citas ────────────────────────────────────────────────
            body = await page.inner_text("body")
            if _no_citas(body):
                return {"success": False, "error": "No hay citas disponibles en este momento"}

            # ── Personal Data ─────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Filling personal data")
            await _fill_field(page,
                ["#txtIdCitado", "input[name*='nie']", "input[id*='nie']", "input[id*='docId']"],
                data["nie"])
            await _fill_field(page,
                ["#txtDesCitado", "input[name*='nombre']", "input[id*='nombre']"],
                data["nombre"])
            await _fill_field(page,
                ["input[name*='apellido']", "input[id*='apellido']"],
                data["apellido"])
            await _fill_field(page,
                ["input[type='email']", "input[name*='email']", "input[id*='email']"],
                data["email"])
            await _fill_field(page,
                ["input[name*='telf']", "input[id*='telf']", "input[name*='phone']"],
                data["telefono"])
            await _fill_field(page,
                ["input[name*='fecha']", "input[id*='fecha']", "input[type='date']"],
                data["fecha_nac"])

            await _click_next(page)
            await _handle_captcha(page, booking_id)

            # ── OTP ───────────────────────────────────────────────────────────
            body = await page.inner_text("body")
            if any(w in body.lower() for w in ["código", "sms", "otp", "verificacion"]):
                logger.info(f"[{booking_id}] OTP required")
                if bot and chat_id and db:
                    otp = await wait_for_otp(bot, chat_id, booking_id, db)
                    if otp:
                        await _fill_field(page,
                            ["input[name*='codigo']", "input[name*='otp']",
                             "input[name*='sms']",    "input[type='number']"], otp)
                        await _click_next(page)

            # ── Pick Slot ─────────────────────────────────────────────────────
            logger.info(f"[{booking_id}] Looking for slots ({date_from} → {date_to})")
            body = await page.inner_text("body")
            if _no_citas(body):
                return {"success": False, "error": "No hay citas disponibles en este momento"}

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
                    logger.info(f"[{booking_id}] Slot clicked: {slot_text}")
                    await page.wait_for_timeout(1500)
                    break

            if not slot_clicked and slot_count > 0:
                await slots.first.click()
                await page.wait_for_timeout(1500)

            await _click_next(page)
            await _handle_captcha(page, booking_id)
            await page.wait_for_timeout(3000)

            # ── Confirmation ──────────────────────────────────────────────────
            final_body = await page.inner_text("body")
            if _no_citas(final_body):
                return {"success": False, "error": "No hay citas en el rango de fechas seleccionado"}

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
                    "success":      True,
                    "fecha":        fecha_str,
                    "hora":         hora_str,
                    "confirmation": conf,
                    "oficina":      oficina_name,
                    "pdf_path":     pdf_path,
                }
            else:
                await page.screenshot(path=f"debug_{booking_id}.png")
                return {"success": False, "error": "No se pudo confirmar la cita. Intenta manualmente."}

        except PWTimeout:
            return {"success": False, "error": "Timeout en la web del gobierno"}
        except Exception as e:
            logger.error(f"Playwright error [{booking_id}]: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await browser.close()


# ─── Auto Select Office (ANY mode) ───────────────────────────────────────────

async def _auto_select_office(page, booking_id: str) -> str:
    """
    Website pe jo bhi pehli available office ho automatically select karo.
    Returns selected office name or empty string if failed.
    """
    await page.wait_for_timeout(1500)

    # Strategy 1: Select dropdown — pick first non-empty option
    selects = page.locator("select#oficina, select[name='oficina'], select[id*='ofic'], select[name*='ofic']")
    if await selects.count() > 0:
        sel = selects.first
        if await sel.is_visible():
            # Get all options
            options = await sel.locator("option").all()
            for opt in options:
                val = await opt.get_attribute("value")
                txt = await opt.inner_text()
                # Skip empty/placeholder options
                if val and val not in ["", "0", "-1"] and txt.strip() and "selecciona" not in txt.lower():
                    await sel.select_option(value=val)
                    logger.info(f"[{booking_id}] Dropdown office selected: {txt.strip()}")
                    await page.wait_for_timeout(1000)
                    return txt.strip()

    # Strategy 2: Radio buttons — click first one
    radios = page.locator("input[type='radio'][name*='oficina'], input[type='radio'][id*='oficina']")
    if await radios.count() > 0:
        first_radio = radios.first
        label_for = await first_radio.get_attribute("id")
        office_txt = ""
        if label_for:
            label = page.locator(f"label[for='{label_for}']")
            if await label.count() > 0:
                office_txt = await label.inner_text()
        await first_radio.click()
        logger.info(f"[{booking_id}] Radio office selected: {office_txt}")
        await page.wait_for_timeout(1000)
        return office_txt.strip() or "Oficina seleccionada"

    # Strategy 3: Table rows with office names — click first
    rows = page.locator("table tr:has(input[type='radio']), .oficina-item, li.oficina")
    if await rows.count() > 0:
        first_row = rows.first
        txt = await first_row.inner_text()
        radio = first_row.locator("input[type='radio']")
        if await radio.count() > 0:
            await radio.click()
        else:
            await first_row.click()
        logger.info(f"[{booking_id}] Row office selected: {txt[:60]}")
        await page.wait_for_timeout(1000)
        return txt[:60].strip()

    # Strategy 4: Any clickable office link/button
    office_links = page.locator("a[href*='ofic'], button[class*='ofic'], .oficina a")
    if await office_links.count() > 0:
        txt = await office_links.first.inner_text()
        await office_links.first.click()
        logger.info(f"[{booking_id}] Link office selected: {txt}")
        await page.wait_for_timeout(1000)
        return txt.strip()

    logger.warning(f"[{booking_id}] Could not find office selector on page")
    return ""


async def _select_specific_office(page, oficina_idx: int, oficina_name: str, booking_id: str):
    """Select a specific office by index"""
    await page.wait_for_timeout(1000)

    # Try select dropdown by index
    sel = page.locator("select#oficina, select[name='oficina'], select[id*='ofic']").first
    if await sel.count() > 0 and await sel.is_visible():
        try:
            await sel.select_option(index=oficina_idx)
            await page.wait_for_timeout(1000)
            return
        except Exception:
            pass

    # Try radio buttons by index
    radios = page.locator("input[type='radio']")
    if await radios.count() > oficina_idx:
        await radios.nth(oficina_idx).click()
        await page.wait_for_timeout(1000)
        return

    # Try text match
    short = oficina_name.replace("CNP - COMISARIA ", "").replace("CNP - ", "")[:30]
    link = page.locator(f"a:has-text('{short}'), label:has-text('{short}'), td:has-text('{short}')").first
    if await link.count() > 0:
        await link.click()
        await page.wait_for_timeout(1000)


# ─── Helpers ──────────────────────────────────────────────────────────────────

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
        "img[src*='captcha'], img[id*='captcha'], img[class*='captcha'], "
        "img[src*='Captcha'], #captcha img"
    ).first
    if await captcha_img.count() > 0 and await captcha_img.is_visible():
        logger.info(f"[{booking_id}] Captcha detected — solving with 2Captcha")
        img_bytes = await captcha_img.screenshot()
        solution  = await solve_captcha_image(img_bytes)
        if solution:
            inp = page.locator(
                "input[name*='captcha'], input[id*='captcha'], input[name*='Captcha']"
            ).first
            if await inp.count() > 0:
                await inp.fill(solution)
                await page.wait_for_timeout(500)
                await _click_next(page)

def _no_citas(text: str) -> bool:
    phrases = [
        "no hay citas", "no existen citas", "no quedan citas",
        "sin citas disponibles", "no available", "no se han encontrado citas"
    ]
    return any(p in text.lower() for p in phrases)
