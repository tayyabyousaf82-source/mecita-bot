"""
booking.py v4 — Exact same logic as cita-bot-v32 Chrome Extension
Features:
  - Refresh intervals: 1, 3, 5, 7 min + rapid 32-33 sec mode (9 times)
  - Fast refresh at 31-33 sec mark
  - Preferred oficina first priority, then ANY
  - 2Captcha auto-solve (image + reCAPTCHA)
  - OTP: auto-tick checkboxes + notify Telegram + wait for user OTP
  - OTP wrong: retry once, then ask again
  - Track offices with available slots → try more there
  - PDF download → upload to Telegram
  - WAF block detection → clear cookies → restart
  - Session expired → auto-click Aceptar
"""

import asyncio, logging, base64, os, re, time, json
from datetime import datetime, date
from playwright.async_api import async_playwright, TimeoutError as PWTimeout, Page

logger = logging.getLogger(__name__)

BOOKING_URL  = "https://icp.administracionelectronica.gob.es/icpplustieb/index.html"
CAPTCHA_KEY  = os.environ.get("CAPTCHA_API_KEY", "")

# ── Refresh intervals (seconds) ───────────────────────────────────────────────
# Normal mode: 1min, 3min, 5min, 7min cycling
NORMAL_INTERVALS = [60, 180, 300, 420]
# Rapid mode: triggered at 31-33 sec, do 9 fast reloads
RAPID_RELOAD_COUNT   = 9
RAPID_RELOAD_DELAY   = 0.5   # 500ms between rapid reloads
RAPID_TRIGGER_SEC    = 31    # when second hand hits 31-33, go rapid

# ── Office tracking ───────────────────────────────────────────────────────────
# Track which offices had available slots → try them more
office_hit_times: dict = {}   # {office_name: [timestamp, ...]}

# ─────────────────────────────────────────────────────────────────────────────

async def book_appointment(data: dict, bot=None, db=None, booking_id: str = "TEMP") -> dict:
    """Main entry — runs 24/7 retry loop"""
    province_id   = data["province_id"]
    tramite_id    = str(data["tramite_id"])
    oficina_idx   = data.get("oficina_idx", "ANY")
    date_from     = data.get("date_from", "")
    date_to       = data.get("date_to", "")
    chat_id       = int(data.get("telegram_id", 0))
    access_method = data.get("access_method", "sin")
    doc_type      = data.get("doc_type", "NIE")

    # Get preferred office name
    from data import PROVINCIA_DATA
    is_any = str(oficina_idx).upper() == "ANY"
    if is_any:
        preferred_office = ""
        oficina_idx_int  = None
    else:
        oficina_idx_int = int(oficina_idx)
        preferred_office = PROVINCIA_DATA[province_id]["oficinas"][oficina_idx_int]

    interval_idx  = 0
    attempt       = 0
    otp_retry_count = {}   # {booking_id: count}

    while True:
        attempt += 1
        try:
            # Check if cancelled
            if db:
                b = db.get_booking(booking_id)
                if b and b["status"] in ("cancelled", "success"):
                    logger.info(f"[{booking_id}] Booking cancelled/done — stopping")
                    break

            # Pick interval (rapid check based on clock seconds)
            now_sec = datetime.now().second
            if RAPID_TRIGGER_SEC <= now_sec <= 33:
                wait_sec = 0  # do rapid reloads now
            else:
                wait_sec = NORMAL_INTERVALS[interval_idx % len(NORMAL_INTERVALS)]
                interval_idx += 1

            logger.info(f"[{booking_id}] Attempt {attempt} — wait={wait_sec}s")

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage",
                          "--disable-blink-features=AutomationControlled"]
                )
                ctx = await browser.new_context(
                    viewport={"width":1280,"height":900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                )
                page = await ctx.new_page()

                # Stealth: remove webdriver flag
                await page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

                try:
                    result = await _run_booking_flow(
                        page=page, data=data, booking_id=booking_id,
                        province_id=province_id, tramite_id=tramite_id,
                        preferred_office=preferred_office, is_any=is_any,
                        date_from=date_from, date_to=date_to,
                        bot=bot, chat_id=chat_id, db=db,
                        otp_retry_count=otp_retry_count
                    )

                    if result.get("success"):
                        if db: db.update_booking_status(booking_id, "success", result)
                        await _notify_success(bot, chat_id, result, booking_id)
                        return result

                    error = result.get("error", "")
                    if "no hay citas" in error.lower() or "no disponible" in error.lower():
                        # Normal — no slots, retry with rapid mode
                        if db: db.update_booking_status(booking_id, "queued")
                        await _rapid_check(page, booking_id)
                    else:
                        logger.warning(f"[{booking_id}] Error: {error}")
                        if db: db.update_booking_status(booking_id, "queued")

                except PWTimeout:
                    logger.warning(f"[{booking_id}] Timeout")
                except Exception as e:
                    logger.error(f"[{booking_id}] Flow error: {e}")
                finally:
                    await browser.close()

            # Wait for next attempt
            if wait_sec > 0:
                await asyncio.sleep(wait_sec)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[{booking_id}] Worker error: {e}")
            await asyncio.sleep(30)

    return {"success": False, "error": "Booking stopped"}

# ── Rapid reload (32-33 sec trigger) ─────────────────────────────────────────

async def _rapid_check(page: Page, booking_id: str):
    """Do 9 rapid reloads at 500ms intervals when clock hits 31-33 sec"""
    now_sec = datetime.now().second
    if not (RAPID_TRIGGER_SEC <= now_sec <= 33):
        return

    logger.info(f"[{booking_id}] RAPID MODE — {RAPID_RELOAD_COUNT} reloads")
    for i in range(RAPID_RELOAD_COUNT):
        try:
            await page.reload(wait_until="domcontentloaded", timeout=10000)
            body = await page.inner_text("body")
            if _has_slots(body):
                logger.info(f"[{booking_id}] RAPID: slot found on reload {i+1}!")
                return True
        except Exception:
            pass
        await asyncio.sleep(RAPID_RELOAD_DELAY)

    # After 9 rapid reloads → 30 sec pause
    logger.info(f"[{booking_id}] RAPID done — 30s pause")
    await asyncio.sleep(30)

# ── Main booking flow ─────────────────────────────────────────────────────────

async def _run_booking_flow(
    page, data, booking_id, province_id, tramite_id,
    preferred_office, is_any, date_from, date_to,
    bot, chat_id, db, otp_retry_count
) -> dict:

    # Load page
    logger.info(f"[{booking_id}] Loading {BOOKING_URL}")
    try:
        await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
    except Exception:
        await page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(1500)

    # Check WAF block
    body = await page.inner_text("body")
    if _is_waf_blocked(body):
        await _clear_cookies_reload(page)
        return {"success": False, "error": "WAF block — restarted"}

    # Accept cookies
    await _dismiss_cookies(page)

    # ── STEP 1: Province ──────────────────────────────────────────
    await _select_province(page, province_id, booking_id)

    # ── STEP 2: Tramite ───────────────────────────────────────────
    await _select_tramite(page, tramite_id, data, booking_id)

    # ── STEP 3: acInfo (Sin/Con Clave) ────────────────────────────
    await _handle_acinfo(page, data.get("access_method","sin"), booking_id)

    # ── STEP 4: Personal data ─────────────────────────────────────
    await _fill_personal_data(page, data, booking_id)

    # ── STEP 5: Solicitar Cita ────────────────────────────────────
    await _click_solicitar_cita(page, booking_id)

    # ── STEP 6: Select Oficina ────────────────────────────────────
    body = await page.inner_text("body")
    if _no_citas(body):
        return {"success": False, "error": "No hay citas disponibles"}

    office_selected = await _select_oficina(page, preferred_office, is_any, booking_id)
    if not office_selected:
        return {"success": False, "error": f"No hay citas disponibles para oficina"}

    await _click_siguiente(page)
    await _handle_captcha(page, booking_id)

    # ── STEP 7: Select slot (LIBRE) ───────────────────────────────
    body = await page.inner_text("body")
    if _no_citas(body):
        return {"success": False, "error": "No hay citas disponibles"}

    slot_ok = await _select_best_slot(page, date_from, date_to, office_selected, booking_id)
    if not slot_ok:
        return {"success": False, "error": "No hay slots en el rango de fechas"}

    await page.wait_for_timeout(3000)
    await _click_siguiente(page)
    await _handle_captcha(page, booking_id)

    # ── STEP 8: Contact info ──────────────────────────────────────
    await _fill_contact_info(page, data, booking_id)

    # ── STEP 9: OTP ───────────────────────────────────────────────
    body = await page.inner_text("body")
    if _is_otp_page(body, page.url):
        otp_result = await _handle_otp(page, bot, chat_id, booking_id, db, otp_retry_count)
        if not otp_result:
            return {"success": False, "error": "OTP failed"}

    # ── STEP 10: Confirmation ─────────────────────────────────────
    await page.wait_for_timeout(3000)
    body = await page.inner_text("body")
    return await _extract_confirmation(page, body, booking_id)

# ── Step 1: Province ──────────────────────────────────────────────────────────

async def _select_province(page: Page, province_id: str, booking_id: str):
    from data import PROVINCIA_DATA
    pname = PROVINCIA_DATA[province_id]["name"]
    logger.info(f"[{booking_id}] Province: {pname}")

    for attempt in range(20):
        # Try select dropdown
        sel = await page.query_selector("select#provincia, select[name='provincia']")
        if sel:
            await sel.select_option(value=province_id)
            await page.wait_for_timeout(500)
            await _click_siguiente(page)
            return

        # Try radio
        radios = await page.query_selector_all("input[type='radio']")
        for r in radios:
            label_id = await r.get_attribute("id")
            if label_id:
                label = await page.query_selector(f"label[for='{label_id}']")
                if label:
                    txt = await label.inner_text()
                    if pname.lower() in txt.lower():
                        await r.click()
                        await page.wait_for_timeout(400)
                        await _click_siguiente(page)
                        return
        await page.wait_for_timeout(400)

# ── Step 2: Tramite ───────────────────────────────────────────────────────────

async def _select_tramite(page: Page, tramite_id: str, data: dict, booking_id: str):
    from data import PROVINCIA_DATA
    pid   = data["province_id"]
    tidx  = int(tramite_id) if tramite_id.isdigit() else 0
    tname = PROVINCIA_DATA[pid]["tramites"][tidx]
    tname_short = tname[:30].lower()
    logger.info(f"[{booking_id}] Tramite: {tname[:40]}")

    # Reset refresh counter (same as bot.js step2_Tramite)
    for attempt in range(20):
        found = False
        # Try select
        selects = await page.query_selector_all("select")
        for sel in selects:
            opts = await sel.query_selector_all("option")
            for i, opt in enumerate(opts):
                txt = (await opt.inner_text()).lower().strip()
                if tname_short[:20] in txt and len(txt) > 3:
                    await sel.select_option(index=i)
                    found = True
                    break
            if found: break

        # Try radio
        if not found:
            radios = await page.query_selector_all("input[type='radio']")
            for r in radios:
                label_id = await r.get_attribute("id")
                if label_id:
                    label = await page.query_selector(f"label[for='{label_id}']")
                    if label:
                        txt = (await label.inner_text()).lower()
                        if tname_short[:15] in txt:
                            await r.click()
                            found = True
                            break

        if found:
            await page.wait_for_timeout(650)
            await _click_siguiente(page)
            return
        await page.wait_for_timeout(400)

# ── Step 3: acInfo (Entrar / Sin Clave) ──────────────────────────────────────

async def _handle_acinfo(page: Page, access_method: str, booking_id: str):
    await page.wait_for_timeout(800)
    body = await page.inner_text("body")
    body_lower = body.lower()

    # If this is an info page with Entrar button
    if "entrar" in body_lower or "acinfo" in page.url.lower():
        for kw in ["Entrar", "Aceptar", "Siguiente"]:
            try:
                btn = await page.query_selector(f"input[value='{kw}'], button:has-text('{kw}')")
                if btn and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    return
            except Exception:
                pass

    # Sin/Con Clave selection
    if "sin cl@ve" in body_lower or "sin clave" in body_lower:
        if access_method == "con":
            await _click_text(page, "con cl@ve") or await _click_text(page, "con clave")
        else:
            await _click_text(page, "sin cl@ve") or await _click_text(page, "sin clave")
        await page.wait_for_timeout(500)

# ── Step 4: Personal data ─────────────────────────────────────────────────────

async def _fill_personal_data(page: Page, data: dict, booking_id: str):
    await page.wait_for_timeout(500)
    body = await page.inner_text("body")

    if "n.i.e" not in body.lower() and "tipo de documento" not in body.lower():
        return  # Not on personal data page

    logger.info(f"[{booking_id}] Filling personal data")
    doc_type = data.get("doc_type", "NIE")
    nie      = data.get("nie", "")
    nombre   = data.get("nombre", "").upper()
    fnac     = data.get("fecha_nac", "")
    pais     = data.get("nacionalidad", "")

    # ── Select doc type radio (double-click like bot.js) ──
    doc_kws = {"NIE": ["nie","n.i.e"], "DNI": ["d.n.i","dni"], "PASAPORTE": ["pasaporte","passport"]}
    for kw in doc_kws.get(doc_type, ["nie"]):
        radios = await page.query_selector_all("input[type='radio']")
        for r in radios:
            rid = await r.get_attribute("id") or ""
            label = await page.query_selector(f"label[for='{rid}']")
            lbl_txt = (await label.inner_text() if label else "").lower()
            if kw in lbl_txt:
                await r.click()
                await asyncio.sleep(0.12)
                await r.click()  # double click like bot.js
                break

    # ── Fill NIE ──
    nie_el = await _find_input(page, [
        "input[name*='IdCitado']","input[id*='IdCitado']",
        "input[name*='nie' i]","input[id*='nie' i]",
    ])
    if nie_el: await _set_value(page, nie_el, nie.upper())

    # ── Fill Nombre (UPPERCASE, smart paste: don't overwrite with NIE) ──
    nom_el = await _find_input(page, [
        "input[name*='DesCitado']","input[id*='DesCitado']",
        "input[name*='nombre' i]","input[id*='nombre' i]",
    ])
    if nom_el and nom_el != nie_el:
        await _set_value(page, nom_el, nombre)

    # ── Fill birth year ──
    year = _extract_year(fnac)
    if year:
        ano_el = await _find_input(page, [
            "input[name*='anyo' i]","input[id*='anyo' i]",
            "input[name*='nacimiento' i]","input[placeholder*='aaaa' i]",
        ])
        if ano_el: await _set_value(page, ano_el, year)

    # ── Fill country ──
    if pais:
        pais_sel = await page.query_selector(
            "select[name*='pais' i], select[id*='pais' i], select[name*='nacion' i]"
        )
        if pais_sel:
            opts = await pais_sel.query_selector_all("option")
            for opt in opts:
                txt = (await opt.inner_text()).lower()
                if pais.lower()[:6] in txt:
                    val = await opt.get_attribute("value")
                    await pais_sel.select_option(value=val)
                    break

    await page.wait_for_timeout(1550)
    await _click_siguiente(page)

# ── Step 5: Solicitar Cita ────────────────────────────────────────────────────

async def _click_solicitar_cita(page: Page, booking_id: str):
    await page.wait_for_timeout(500)
    for attempt in range(10):
        if await _click_text(page, "solicitar cita"):
            logger.info(f"[{booking_id}] Solicitar Cita clicked")
            return
        await page.wait_for_timeout(400)

# ── Step 6: Select Oficina ────────────────────────────────────────────────────

async def _select_oficina(page: Page, preferred_office: str, is_any: bool, booking_id: str) -> str:
    """
    Priority:
    1. Preferred office (if specified)
    2. Office with recent slot hits (tracked)
    3. Any first available (if ANY mode)
    Returns selected office name or ""
    """
    await page.wait_for_timeout(1500)

    # Check if cita radio cards already on page (skip oficina step)
    if await _has_cita_cards(page):
        logger.info(f"[{booking_id}] Cita cards found — skipping oficina step")
        return "any"

    # Get oficina select
    ofic_sel = await _get_oficina_select(page)
    if not ofic_sel:
        logger.info(f"[{booking_id}] No oficina selector — proceeding")
        return "any"

    opts = await ofic_sel.query_selector_all("option")

    # Filter real options
    real_opts = []
    for opt in opts:
        val = await opt.get_attribute("value") or ""
        txt = (await opt.inner_text()).strip()
        if val and val not in ("","0","-1") and txt and "seleccione" not in txt.lower():
            real_opts.append((val, txt))

    if not real_opts:
        return ""

    # Priority 1: Preferred office
    if preferred_office and not is_any:
        pref_short = preferred_office[:15].lower()
        for val, txt in real_opts:
            if pref_short in txt.lower() or txt.lower()[:15] in preferred_office.lower():
                await ofic_sel.select_option(value=val)
                logger.info(f"[{booking_id}] Preferred office: {txt}")
                _track_office_hit(txt)
                await page.wait_for_timeout(100)
                return txt

        # Preferred not found — wait and retry (like bot.js rapidReloadOficina removed in v14)
        logger.info(f"[{booking_id}] Preferred office not found in dropdown")

    # Priority 2: Office with most recent hits
    if office_hit_times:
        for val, txt in real_opts:
            for hit_office in office_hit_times:
                if txt.lower()[:10] in hit_office.lower():
                    await ofic_sel.select_option(value=val)
                    logger.info(f"[{booking_id}] Hit-tracked office: {txt}")
                    return txt

    # Priority 3: ANY — first real option
    val0, txt0 = real_opts[0]
    await ofic_sel.select_option(value=val0)

    # Force-set with JS (like bot.js CUALQUIER mode)
    await page.evaluate(f"""(sel) => {{
        sel.value = '{val0}';
        sel.dispatchEvent(new Event('input', {{bubbles:true}}));
        sel.dispatchEvent(new Event('change', {{bubbles:true}}));
    }}""", ofic_sel)

    await page.wait_for_timeout(200)
    logger.info(f"[{booking_id}] ANY office: {txt0}")
    return txt0

def _track_office_hit(office_name: str):
    if office_name not in office_hit_times:
        office_hit_times[office_name] = []
    office_hit_times[office_name].append(time.time())
    # Keep only last 10 hits
    office_hit_times[office_name] = office_hit_times[office_name][-10:]

# ── Step 7: Select best slot (LIBRE) ─────────────────────────────────────────

async def _select_best_slot(page: Page, date_from: str, date_to: str,
                             office_name: str, booking_id: str) -> bool:
    """
    Find LIBRE slots, pick best one in date range.
    Same logic as bot.js clickLibreAndConfirm + selectBestCita
    """
    await page.wait_for_timeout(500)

    # Check calendar page first
    if await _is_calendar_page(page):
        logger.info(f"[{booking_id}] Calendar page — clicking date in range")
        clicked = await _click_calendar_date(page, date_from, date_to)
        if clicked:
            await page.wait_for_timeout(1500)

    # Find LIBRE cells
    libre_slots = await _find_libre_slots(page)
    if not libre_slots:
        # Check for radio cita cards (alternative slot format)
        return await _select_cita_radio(page, date_from, date_to, booking_id)

    # Filter by date range
    use_range = bool(date_from and date_to)
    range_start = _date_to_num(date_from)
    range_end   = _date_to_num(date_to)

    best = None
    best_num = float('inf')

    for slot in libre_slots:
        slot_date = slot.get("date")
        if use_range and slot_date:
            n = _date_to_num(slot_date)
            if n and range_start <= n <= range_end and n < best_num:
                best_num = n
                best = slot
        elif not use_range:
            best = slot
            break

    if not best and libre_slots:
        best = libre_slots[0]  # fallback

    if best:
        el = best["el"]
        logger.info(f"[{booking_id}] LIBRE clicked: {best.get('date','?')}")
        if office_name:
            _track_office_hit(office_name)
        await el.click()
        await page.wait_for_timeout(3000)  # 3s wait like bot.js
        await _click_siguiente(page)
        return True

    return False

async def _find_libre_slots(page: Page) -> list:
    """Find all LIBRE cells — same as bot.js getAllLibre"""
    results = []

    # Method 1: Table column-based (same as bot.js)
    tables = await page.query_selector_all("table")
    for table in tables:
        rows = await table.query_selector_all("tr")
        if len(rows) < 2: continue

        # Find header row with dates
        header_dates = {}
        for row in rows:
            cells = await row.query_selector_all("td, th")
            has_date = False
            for i, cell in enumerate(cells):
                txt = await cell.inner_text()
                m = re.search(r"\d{2}/\d{2}/\d{4}", txt)
                if m:
                    header_dates[i] = m.group()
                    has_date = True
            if has_date: break

        # Find LIBRE cells
        for row in rows:
            cells = await row.query_selector_all("td, th")
            for i, cell in enumerate(cells):
                txt = (await cell.inner_text()).strip().upper()
                if txt == "LIBRE":
                    results.append({
                        "el": cell,
                        "date": header_dates.get(i) or header_dates.get(max([k for k in header_dates if k<=i], default=0))
                    })

    # Method 2: Generic fallback
    if not results:
        for tag in ["td","a","button","span","div"]:
            els = await page.query_selector_all(tag)
            for el in els:
                txt = (await el.inner_text()).strip().upper()
                if txt == "LIBRE":
                    results.append({"el": el, "date": None})

    return results

async def _select_cita_radio(page: Page, date_from: str, date_to: str, booking_id: str) -> bool:
    """Select best radio-button cita card (like bot.js selectBestCita)"""
    range_start = _date_to_num(date_from)
    range_end   = _date_to_num(date_to)
    use_range   = bool(date_from and date_to)

    radios = await page.query_selector_all("input[type='radio']:not([disabled])")
    best_radio = None
    best_num   = float('inf')

    for radio in radios:
        # Walk up DOM to find date text (like bot.js walk-up logic)
        date_str = None
        node = radio
        for _ in range(8):
            try:
                parent = await node.query_selector("xpath=..")
                if not parent: break
                txt = await parent.inner_text()
                m = re.search(r"\d{2}/\d{2}/\d{4}", txt)
                if m:
                    date_str = m.group()
                    break
                node = parent
            except Exception:
                break

        if not date_str: continue

        n = _date_to_num(date_str)
        if use_range:
            if n and range_start <= n <= range_end and n < best_num:
                best_num   = n
                best_radio = radio
        else:
            best_radio = radio
            break

    if best_radio:
        await best_radio.click()
        await page.wait_for_timeout(3000)
        await _click_siguiente(page)
        logger.info(f"[{booking_id}] Cita radio selected")
        return True

    logger.info(f"[{booking_id}] No cita radio in range {date_from}-{date_to}")
    return False

async def _is_calendar_page(page: Page) -> bool:
    body = await page.inner_text("body")
    body_lower = body.lower()
    has_text = any(t in body_lower for t in [
        "selecciona una de las siguientes citas",
        "citas disponibles","elija una de las siguientes"
    ])
    if not has_text: return False
    dp = await page.query_selector("a.ui-state-default")
    return dp is not None

async def _click_calendar_date(page: Page, date_from: str, date_to: str) -> bool:
    """Click best day in jQuery UI datepicker (same logic as bot.js clickCalendarDateInRange)"""
    range_start = _date_to_num(date_from)
    range_end   = _date_to_num(date_to)
    use_range   = bool(date_from and date_to)

    # Get month/year from datepicker
    month_el = await page.query_selector(".ui-datepicker-month")
    year_el  = await page.query_selector(".ui-datepicker-year")
    if not month_el or not year_el: return False

    MONTHS = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
              "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}

    cal_month = MONTHS.get((await month_el.inner_text()).strip().lower(), 0)
    cal_year  = int((await year_el.inner_text()).strip() or "0")
    if not cal_month or not cal_year: return False

    # Get clickable day cells
    anchors = await page.query_selector_all("a.ui-state-default")
    today   = datetime.now()
    today_key = today.year*10000 + (today.month)*100 + today.day

    best_cell = None
    best_key  = float('inf')

    for anchor in anchors:
        td = await anchor.query_selector("xpath=..")
        if td:
            td_cls = await td.get_attribute("class") or ""
            if "unselectable" in td_cls or "disabled" in td_cls: continue

        day = int((await anchor.inner_text()).strip())
        ck  = cal_year*10000 + cal_month*100 + day

        if use_range:
            if range_start <= ck <= range_end and ck < best_key:
                best_key  = ck
                best_cell = anchor
        elif ck >= today_key and ck < best_key:
            best_key  = ck
            best_cell = anchor

    if best_cell:
        await best_cell.click()
        await page.wait_for_timeout(500)
        return True
    return False

# ── Step 8: Contact info ──────────────────────────────────────────────────────

async def _fill_contact_info(page: Page, data: dict, booking_id: str):
    await page.wait_for_timeout(500)
    body = await page.inner_text("body")
    if "teléfono" not in body.lower() and "correo" not in body.lower():
        return

    logger.info(f"[{booking_id}] Filling contact info")
    tel   = data.get("telefono","")
    email = data.get("email","")

    tel_el = await _find_input(page, [
        "input[name*='Telefono' i]","input[id*='Telefono' i]","input[type='tel']"
    ])
    if tel_el and tel: await _set_value(page, tel_el, tel)

    # Fill both email + repeat email fields
    email_els = await page.query_selector_all("input[type='email']")
    if not email_els:
        email_els = await page.query_selector_all(
            "input[name*='mail' i], input[id*='mail' i], input[name*='email' i]"
        )
    for el in email_els:
        if email: await _set_value(page, el, email)

    # Tick all checkboxes
    cbs = await page.query_selector_all("input[type='checkbox']")
    for cb in cbs:
        checked = await cb.is_checked()
        if not checked:
            await cb.click()

    # Wait for Siguiente to be enabled (max 1.4s)
    await page.wait_for_timeout(1420)
    await _click_siguiente(page)

# ── Step 9: OTP ───────────────────────────────────────────────────────────────

async def _handle_otp(page: Page, bot, chat_id: int, booking_id: str,
                      db, otp_retry_count: dict) -> bool:
    """
    1. Auto-tick all checkboxes
    2. Send screenshot + notification to Telegram
    3. Wait for user to send OTP
    4. Fill OTP + confirm
    5. If wrong → retry once → ask again
    """
    logger.info(f"[{booking_id}] OTP page detected")

    # Auto-tick checkboxes (same as bot.js step9_OTP)
    await _tick_all_checkboxes(page)
    await page.wait_for_timeout(500)
    await _tick_all_checkboxes(page)

    # Send screenshot to Telegram
    if bot and chat_id:
        try:
            screenshot = await page.screenshot()
            await bot.send_photo(
                chat_id, photo=screenshot,
                caption=(
                    "📱 *OTP REQUERIDO!*\n\n"
                    "El bot llegó a la página de verificación SMS.\n"
                    "Por favor envía el *código OTP* que recibiste.\n"
                    "_(Solo los números, ej: `123456`)_"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            if bot and chat_id:
                await bot.send_message(
                    chat_id,
                    "📱 *OTP REQUERIDO!*\n\nEnvía el código SMS que recibiste.",
                    parse_mode="Markdown"
                )

    if not db: return False

    # Wait for OTP (5 minutes)
    otp = await _wait_for_otp(bot, chat_id, booking_id, db, timeout=300)
    if not otp: return False

    # Fill OTP
    otp_el = await _find_otp_input(page)
    if otp_el:
        await _set_value(page, otp_el, otp)
        await _tick_all_checkboxes(page)
        await page.wait_for_timeout(600)
        await _click_kw(page, ["enviar","aceptar","confirmar"])
        await page.wait_for_timeout(2000)

        # Check if OTP was wrong
        body = await page.inner_text("body")
        if any(w in body.lower() for w in ["incorrecto","inválido","error","wrong","invalid"]):
            logger.warning(f"[{booking_id}] OTP wrong!")

            retry_count = otp_retry_count.get(booking_id, 0)
            if retry_count < 1:
                # Retry once automatically
                otp_retry_count[booking_id] = retry_count + 1
                if bot and chat_id:
                    await bot.send_message(
                        chat_id,
                        "❌ *OTP incorrecto.* Intentando de nuevo...\n\nEnvía el código correcto:",
                        parse_mode="Markdown"
                    )
                otp2 = await _wait_for_otp(bot, chat_id, booking_id, db, timeout=120)
                if otp2 and otp_el:
                    await _set_value(page, otp_el, otp2)
                    await _tick_all_checkboxes(page)
                    await page.wait_for_timeout(600)
                    await _click_kw(page, ["enviar","aceptar","confirmar"])
                    await page.wait_for_timeout(2000)
            else:
                # Ask user again
                if bot and chat_id:
                    await bot.send_message(
                        chat_id,
                        "❌ *OTP incorrecto.*\n\nEnvía el código correcto:",
                        parse_mode="Markdown"
                    )
                return False

    return True

async def _tick_all_checkboxes(page: Page):
    """Auto-tick all checkboxes (like bot.js tickAllCheckboxes)"""
    cbs = await page.query_selector_all("input[type='checkbox']")
    for cb in cbs:
        if not await cb.is_checked():
            try:
                await cb.click()
                await page.wait_for_timeout(50)
            except Exception:
                pass

async def _wait_for_otp(bot, chat_id: int, booking_id: str, db, timeout: int = 300) -> str:
    """Notify user and wait for OTP code"""
    await bot.send_message(
        chat_id,
        f"⏳ Esperando tu código OTP...\n_(Tienes {timeout//60} minutos)_",
        parse_mode="Markdown"
    )
    for _ in range(timeout // 3):
        await asyncio.sleep(3)
        row = db.get_pending_otp(booking_id)
        if row:
            db.mark_otp_used(booking_id)
            await bot.send_message(chat_id, "✅ *OTP recibido! Confirmando...*", parse_mode="Markdown")
            return row["otp_code"]
    await bot.send_message(chat_id, "⏰ *Tiempo agotado esperando OTP.*", parse_mode="Markdown")
    return ""

async def _find_otp_input(page: Page):
    return await _find_input(page, [
        "input[name*='odigo' i]","input[id*='odigo' i]",
        "input[name*='otp' i]","input[name*='sms' i]",
        "input[maxlength='6']","input[maxlength='4']",
        "input[name*='verificacion' i]",
    ])

# ── Confirmation ──────────────────────────────────────────────────────────────

async def _extract_confirmation(page: Page, body: str, booking_id: str) -> dict:
    if _no_citas(body):
        return {"success": False, "error": "No hay citas en el rango"}

    confirmed = any(w in body.lower() for w in [
        "cita confirmada","cita reservada","ha sido reservada",
        "localizador","número de su cita"
    ])

    fecha = re.search(r"\d{2}/\d{2}/\d{4}", body)
    hora  = re.search(r"\d{2}:\d{2}", body)
    loc   = re.search(r"[Ll]ocalizador[:\s]+([A-Z0-9\-]+)", body)

    fecha_str = fecha.group() if fecha else ""
    hora_str  = hora.group()  if hora  else ""
    conf      = loc.group(1)  if loc   else ""

    pdf_path = ""
    if confirmed or fecha_str:
        try:
            os.makedirs("pdfs", exist_ok=True)
            pdf_path = f"pdfs/cita_{booking_id}.pdf"
            await page.pdf(path=pdf_path, format="A4", print_background=True)
        except Exception as e:
            logger.warning(f"PDF error: {e}")

    if confirmed or fecha_str or conf:
        return {"success":True,"fecha":fecha_str,"hora":hora_str,
                "confirmation":conf,"pdf_path":pdf_path}

    # Debug screenshot
    try: await page.screenshot(path=f"debug_{booking_id}.png")
    except Exception: pass
    return {"success":False,"error":"Confirmation not detected"}

async def _notify_success(bot, chat_id: int, result: dict, booking_id: str):
    if not bot or not chat_id: return
    try:
        await bot.send_message(
            chat_id,
            f"🎉 *¡CITA RESERVADA!*\n\n"
            f"📅 Fecha: *{result.get('fecha','')}*\n"
            f"🕐 Hora: *{result.get('hora','')}*\n"
            f"🔖 Localizador: `{result.get('confirmation','')}`\n\n"
            f"✅ ¡Enhorabuena! Tu cita ha sido confirmada.",
            parse_mode="Markdown"
        )
        pdf = result.get("pdf_path","")
        if pdf and os.path.exists(pdf):
            with open(pdf,"rb") as f:
                await bot.send_document(
                    chat_id, f,
                    filename=f"cita_{booking_id}.pdf",
                    caption="📄 Justificante de cita"
                )
    except Exception as e:
        logger.error(f"Notify error: {e}")

# ── Captcha ───────────────────────────────────────────────────────────────────

async def _handle_captcha(page: Page, booking_id: str):
    """Handle both image captcha and reCAPTCHA (same as bot.js)"""
    # Image captcha
    captcha_img = await page.query_selector(
        "img[src*='captcha' i], img[id*='captcha' i], img[class*='captcha' i]"
    )
    if captcha_img and await captcha_img.is_visible():
        logger.info(f"[{booking_id}] Image captcha detected")
        if CAPTCHA_KEY:
            img_bytes = await captcha_img.screenshot()
            solution  = await _solve_image_captcha(img_bytes)
            if solution:
                inp = await _find_input(page, [
                    "input[name*='captcha' i]","input[id*='captcha' i]"
                ])
                if inp:
                    await _set_value(page, inp, solution)
                    await page.wait_for_timeout(500)
                    await _click_siguiente(page)
        return

    # reCAPTCHA
    rc = await page.query_selector(".g-recaptcha, [data-sitekey]")
    if rc:
        site_key = await rc.get_attribute("data-sitekey") or ""
        if site_key and CAPTCHA_KEY:
            logger.info(f"[{booking_id}] reCAPTCHA detected")
            token = await _solve_recaptcha(site_key, page.url)
            if token:
                await page.evaluate(f"""
                    var ta = document.getElementById('g-recaptcha-response');
                    if (!ta) {{ ta = document.createElement('textarea'); ta.id='g-recaptcha-response'; ta.name='g-recaptcha-response'; document.body.appendChild(ta); }}
                    ta.value = '{token}';
                    var rcEl = document.querySelector('[data-callback]');
                    if (rcEl) {{ var cb = rcEl.getAttribute('data-callback'); if (cb && window[cb]) window[cb]('{token}'); }}
                """)
                await page.wait_for_timeout(1000)
                await _click_siguiente(page)

async def _solve_image_captcha(img_bytes: bytes) -> str:
    import httpx
    if not CAPTCHA_KEY: return ""
    b64 = base64.b64encode(img_bytes).decode()
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post("https://2captcha.com/in.php", data={
            "key":CAPTCHA_KEY,"method":"base64","body":b64,"json":1
        })
        data = r.json()
        if data.get("status") != 1: return ""
        tid = data["request"]
        for _ in range(24):
            await asyncio.sleep(5)
            res = (await client.get(f"https://2captcha.com/res.php?key={CAPTCHA_KEY}&action=get&id={tid}&json=1")).json()
            if res.get("status") == 1: return res["request"]
            if res.get("request") != "CAPCHA_NOT_READY": return ""
    return ""

async def _solve_recaptcha(site_key: str, page_url: str) -> str:
    import httpx
    if not CAPTCHA_KEY: return ""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post("https://2captcha.com/in.php", data={
            "key":CAPTCHA_KEY,"method":"userrecaptcha",
            "googlekey":site_key,"pageurl":page_url,"json":1
        })
        data = r.json()
        if data.get("status") != 1: return ""
        tid = data["request"]
        for _ in range(18):
            await asyncio.sleep(5)
            res = (await client.get(f"https://2captcha.com/res.php?key={CAPTCHA_KEY}&action=get&id={tid}&json=1")).json()
            if res.get("status") == 1: return res["request"]
            if res.get("request") != "CAPCHA_NOT_READY": return ""
    return ""

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _click_siguiente(page: Page):
    for kw in ["Aceptar","Siguiente","Continuar","Enviar","Solicitar","Acceder"]:
        try:
            btn = await page.query_selector(f"input[value='{kw}'], button:has-text('{kw}')")
            if btn and await btn.is_visible():
                await btn.click()
                try: await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception: pass
                await page.wait_for_timeout(1000)
                return
        except Exception:
            pass

async def _click_kw(page: Page, kws: list) -> bool:
    for kw in kws:
        try:
            btn = await page.query_selector(f"input[value='{kw}' i], button:has-text('{kw}')")
            if btn and await btn.is_visible():
                await btn.click()
                return True
        except Exception:
            pass
    return False

async def _click_text(page: Page, text: str) -> bool:
    els = await page.query_selector_all("button,input,a,div,span,li,td,label")
    for el in els:
        try:
            txt = (await el.inner_text()).strip().lower()
            if text.lower() in txt and len(txt) < 100:
                await el.click()
                return True
        except Exception:
            pass
    return False

async def _find_input(page: Page, selectors: list):
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                return el
        except Exception:
            pass
    return None

async def _set_value(page: Page, el, value: str):
    """React/Angular-safe value setter (same as bot.js setV)"""
    try:
        await page.evaluate("""(args) => {
            var el = args[0], val = args[1];
            var d = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value');
            if(d) d.set.call(el,val); else el.value=val;
            ['input','change'].forEach(ev=>el.dispatchEvent(new Event(ev,{bubbles:true})));
        }""", [el, value])
    except Exception:
        await el.fill(value)

async def _get_oficina_select(page: Page):
    sels = await page.query_selector_all("select")
    for sel in sels:
        sid   = await sel.get_attribute("id") or ""
        sname = await sel.get_attribute("name") or ""
        if re.search(r"oficin|centro|lugar|comisaria", sid+sname, re.I):
            return sel
    # Fallback: first visible select
    for sel in sels:
        if await sel.is_visible():
            return sel
    return None

async def _has_cita_cards(page: Page) -> bool:
    """Check if cita radio cards are on page (date + radio)"""
    radios = await page.query_selector_all("input[type='radio']:not([disabled])")
    for r in radios:
        node = r
        for _ in range(6):
            try:
                parent = await node.query_selector("xpath=..")
                if not parent: break
                txt = await parent.inner_text()
                if re.search(r"\d{2}/\d{2}/\d{4}", txt):
                    return True
                node = parent
            except Exception:
                break
    return False

async def _dismiss_cookies(page: Page):
    for kw in ["Aceptar","Accept","Acceptar"]:
        try:
            btn = await page.query_selector(f"button:has-text('{kw}')")
            if btn and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(500)
                return
        except Exception:
            pass

async def _clear_cookies_reload(page: Page):
    await page.evaluate("document.cookie.split(';').forEach(c=>{document.cookie=c.replace(/^ +/,'').replace(/=.*/,'=;expires='+new Date(0).toUTCString()+';path=')})")
    await page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=20000)

def _is_waf_blocked(body: str) -> bool:
    lower = body.lower()
    return any(t in lower for t in [
        "the requested url was rejected","your support id is",
        "consult with your administrador"
    ])

def _no_citas(body: str) -> bool:
    lower = body.lower()
    return any(t in lower for t in [
        "no hay citas disponibles","en este momento no hay citas",
        "no existen citas","no tiene citas disponibles"
    ])

def _has_slots(body: str) -> bool:
    return "libre" in body.upper() or not _no_citas(body)

def _is_otp_page(body: str, url: str) -> bool:
    lower = body.lower()
    return (
        ("código" in lower and "sms" in lower) or
        "código de verificación" in lower or
        "introduce el código" in lower or
        "acOTP" in url or "acSMS" in url or
        "verificarCodigo" in url
    )

def _date_to_num(ds: str) -> int:
    """Convert date to int YYYYMMDD. Supports YYYY-MM-DD (form) and DD/MM/YYYY (website)."""
    if not ds: return 0
    if "-" in ds:
        parts = ds.split("-")
        if len(parts) != 3: return 0
        try: return int(parts[0])*10000 + int(parts[1])*100 + int(parts[2])
        except Exception: return 0
    parts = ds.split("/")
    if len(parts) != 3: return 0
    try: return int(parts[2])*10000 + int(parts[1])*100 + int(parts[0])
    except Exception: return 0

def _extract_year(fnac: str) -> str:
    if not fnac: return ""
    fnac = fnac.strip()
    if re.match(r"^\d{4}$", fnac): return fnac
    m = re.search(r"\d{2}/\d{2}/(\d{4})", fnac)
    if m: return m.group(1)
    m = re.search(r"^(\d{4})-", fnac)
    if m: return m.group(1)
    m = re.search(r"(\d{4})", fnac)
    if m: return m.group(1)
    return ""

def save_pdf_and_notify():
    pass  # handled inline in _extract_confirmation
