# booking.py — Playwright Auto-Booking for icp.administracionelectronica.gob.es

import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from config import BOOKING_URL, HEADLESS, MAX_RETRIES, RETRY_DELAY
from data import PROVINCIA_DATA

logger = logging.getLogger(__name__)


async def book_appointment(data: dict) -> dict:
    """
    Main booking function. Fills the Spanish gov website form automatically.
    Returns dict with keys:
        success (bool), fecha, hora, oficina, confirmation, error
    """
    province_id  = data["province_id"]
    tramite_id   = data["tramite_id"]
    oficina_idx  = data["oficina_idx"]
    nombre       = data["nombre"]
    apellido     = data["apellido"]
    nie          = data["nie"]
    fecha_nac    = data["fecha_nac"]   # DD/MM/YYYY
    nacionalidad = data["nacionalidad"]
    email        = data["email"]
    telefono     = data["telefono"]

    oficina_name = PROVINCIA_DATA[province_id]["oficinas"][oficina_idx]
    prov_name    = PROVINCIA_DATA[province_id]["name"]

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Booking attempt {attempt}/{MAX_RETRIES} for NIE {nie}")
        try:
            result = await _do_booking(
                province_id=province_id,
                tramite_id=tramite_id,
                oficina_name=oficina_name,
                nombre=nombre,
                apellido=apellido,
                nie=nie,
                fecha_nac=fecha_nac,
                email=email,
                telefono=telefono,
            )
            if result["success"]:
                return result
            if "no hay citas" in result.get("error", "").lower():
                logger.warning(f"No slots available, attempt {attempt}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                continue
            return result  # Other error — don't retry

        except Exception as e:
            logger.error(f"Booking exception attempt {attempt}: {e}")
            if attempt == MAX_RETRIES:
                return {"success": False, "error": str(e)}
            await asyncio.sleep(RETRY_DELAY)

    return {
        "success": False,
        "error": f"No hay citas disponibles en {prov_name} en este momento. Intenta más tarde."
    }


async def _do_booking(
    province_id, tramite_id, oficina_name,
    nombre, apellido, nie, fecha_nac, email, telefono
) -> dict:
    """Playwright automation for the booking website"""

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=HEADLESS,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        try:
            # ── Step 1: Load main page ────────────────────────────────────────
            logger.info("Loading booking website...")
            await page.goto(BOOKING_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # ── Step 2: Select "Extranjería" service ─────────────────────────
            # Click "Entrar" or the main entry button
            entrar = page.locator("text=Entrar", ).first
            if await entrar.is_visible():
                await entrar.click()
                await page.wait_for_load_state("networkidle")

            # Accept cookies if present
            cookie_btn = page.locator("button:has-text('Aceptar'), button:has-text('Accept')")
            if await cookie_btn.count() > 0:
                await cookie_btn.first.click()
                await page.wait_for_timeout(1000)

            # ── Step 3: Select Province ───────────────────────────────────────
            logger.info(f"Selecting province {province_id}...")
            try:
                province_select = page.locator("select#provincia, select[name='provincia'], select[id*='provincia']").first
                await province_select.wait_for(state="visible", timeout=10000)
                await province_select.select_option(value=province_id)
                await page.wait_for_timeout(1500)
            except PlaywrightTimeout:
                # Try alternative — sometimes it's a link-based interface
                prov_link = page.locator(f"a[href*='{province_id}'], button[data-prov='{province_id}']")
                if await prov_link.count() > 0:
                    await prov_link.first.click()
                    await page.wait_for_load_state("networkidle")

            # ── Step 4: Select Tramite ────────────────────────────────────────
            logger.info(f"Selecting tramite {tramite_id}...")
            try:
                tramite_select = page.locator("select#tramite, select[name='tramite'], select[id*='tramite']").first
                await tramite_select.wait_for(state="visible", timeout=10000)
                await tramite_select.select_option(value=tramite_id)
                await page.wait_for_timeout(1500)
            except PlaywrightTimeout:
                logger.warning("Tramite select not found, trying link click")

            # ── Step 5: Click "Aceptar" / next button ────────────────────────
            for btn_text in ["Aceptar", "Siguiente", "Continuar", "Acceder"]:
                btn = page.locator(f"input[value='{btn_text}'], button:has-text('{btn_text}')").first
                if await btn.is_visible():
                    await btn.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                    break

            # ── Step 6: Check for "no hay citas" ─────────────────────────────
            page_text = await page.inner_text("body")
            if any(phrase in page_text.lower() for phrase in [
                "no hay citas", "no existen citas", "no quedan citas",
                "no available appointments", "sin citas"
            ]):
                return {"success": False, "error": "No hay citas disponibles en este momento"}

            # ── Step 7: Fill Personal Data ────────────────────────────────────
            logger.info("Filling personal data...")

            # NIE/Passport
            for selector in ["input[id*='nie'], input[name*='nie'], input[id*='docId']"]:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.fill(nie)
                    break

            # Nombre
            for selector in ["input[id*='nombre'], input[name*='nombre'], input[id*='name']"]:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.fill(nombre)
                    break

            # Apellido
            for selector in ["input[id*='apellido'], input[name*='apellido'], input[id*='surname']"]:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.fill(apellido)
                    break

            # Fecha nacimiento
            for selector in ["input[id*='fecha'], input[name*='fecha'], input[type='date']"]:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    # Convert DD/MM/YYYY → YYYY-MM-DD for date inputs
                    d, m, y = fecha_nac.split("/")
                    await field.fill(f"{y}-{m}-{d}")
                    break

            # Email
            for selector in ["input[type='email'], input[id*='email'], input[name*='email']"]:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.fill(email)
                    break

            # Telefono
            for selector in ["input[id*='telf'], input[id*='phone'], input[name*='telf'], input[name*='phone']"]:
                field = page.locator(selector).first
                if await field.count() > 0 and await field.is_visible():
                    await field.fill(telefono)
                    break

            await page.wait_for_timeout(1000)

            # ── Step 8: Submit form ───────────────────────────────────────────
            for btn_text in ["Aceptar", "Siguiente", "Enviar", "Solicitar"]:
                btn = page.locator(f"input[value='{btn_text}'], button:has-text('{btn_text}')").first
                if await btn.is_visible():
                    await btn.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                    break

            # ── Step 9: Pick appointment slot ─────────────────────────────────
            logger.info("Looking for appointment slots...")

            # Check again for "no citas"
            page_text = await page.inner_text("body")
            if any(phrase in page_text.lower() for phrase in [
                "no hay citas", "no existen citas", "no quedan citas"
            ]):
                return {"success": False, "error": "No hay citas disponibles en este momento"}

            # Try to click first available slot
            slot = page.locator(
                "a.cita-libre, td.libre a, .appointment-slot, input[type='radio']:not([disabled])"
            ).first
            if await slot.count() > 0:
                await slot.click()
                await page.wait_for_timeout(1500)

                # Confirm slot
                for btn_text in ["Aceptar", "Confirmar", "Siguiente"]:
                    btn = page.locator(f"input[value='{btn_text}'], button:has-text('{btn_text}')").first
                    if await btn.is_visible():
                        await btn.click()
                        await page.wait_for_load_state("networkidle")
                        break

            # ── Step 10: Extract confirmation ─────────────────────────────────
            logger.info("Extracting confirmation...")
            await page.wait_for_timeout(3000)
            final_text = await page.inner_text("body")

            # Extract date/time
            import re
            fecha = ""
            hora  = ""
            conf  = ""

            date_match = re.search(r"\d{2}/\d{2}/\d{4}", final_text)
            if date_match:
                fecha = date_match.group()

            time_match = re.search(r"\d{2}:\d{2}", final_text)
            if time_match:
                hora = time_match.group()

            # Look for confirmation/localizador number
            loc_match = re.search(r"[Ll]ocalizador[:\s]+([A-Z0-9\-]+)", final_text)
            if loc_match:
                conf = loc_match.group(1)
            else:
                num_match = re.search(r"[Nn]úmero[:\s]+([A-Z0-9\-]+)", final_text)
                if num_match:
                    conf = num_match.group(1)

            if fecha or conf:
                return {
                    "success": True,
                    "fecha": fecha,
                    "hora": hora,
                    "confirmation": conf,
                    "oficina": oficina_name,
                }
            else:
                # Screenshot for debugging
                await page.screenshot(path=f"debug_{nie}.png")
                return {
                    "success": False,
                    "error": "No se pudo confirmar la cita. Intenta manualmente."
                }

        except PlaywrightTimeout as e:
            logger.error(f"Playwright timeout: {e}")
            return {"success": False, "error": "Tiempo de espera agotado en la web del gobierno"}
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await browser.close()
