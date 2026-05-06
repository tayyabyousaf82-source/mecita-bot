"""
Playwright Monitoring Engine
Polls the ICP appointment system for availability.
STRICT: No CAPTCHA bypass, no security circumvention.
"""
import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import structlog
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

ICP_BASE_URL = "https://icp.administracionelectronica.gob.es/icpplus/index.html"
SCREENSHOTS_DIR = Path("/app/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")


class MonitoringEngine:
    """
    Manages concurrent Playwright monitoring workers.
    Each worker monitors one job (profile).
    """

    def __init__(self):
        self.active_workers: dict[int, asyncio.Task] = {}
        self.stop_signals: dict[int, asyncio.Event] = {}
        self.otp_events: dict[int, asyncio.Event] = {}
        self.otp_values: dict[int, Optional[str]] = {}
        self.max_workers = int(os.environ.get("MAX_CONCURRENT_WORKERS", 5))

    async def run(self):
        """Main loop: polls backend for queued jobs and dispatches workers."""
        logger.info("Monitoring engine started", max_workers=self.max_workers)

        async with async_playwright() as pw:
            self.playwright = pw
            while True:
                try:
                    await self._poll_queued_jobs()
                    await self._clean_finished_workers()
                except Exception as e:
                    logger.error("Engine loop error", error=str(e))
                await asyncio.sleep(5)

    async def _poll_queued_jobs(self):
        """Fetch queued jobs from backend and start workers."""
        if len(self.active_workers) >= self.max_workers:
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{BACKEND_URL}/api/jobs/",
                    params={"status": "queued", "limit": self.max_workers},
                    timeout=10,
                )
                jobs = resp.json()
        except Exception as e:
            logger.warning("Failed to fetch queued jobs", error=str(e))
            return

        for job in jobs:
            job_id = job["id"]
            if job_id not in self.active_workers:
                logger.info("Starting worker for job", job_id=job_id)
                stop_event = asyncio.Event()
                otp_event = asyncio.Event()
                self.stop_signals[job_id] = stop_event
                self.otp_events[job_id] = otp_event
                self.otp_values[job_id] = None

                task = asyncio.create_task(
                    self._run_job_worker(job_id, job, stop_event, otp_event)
                )
                self.active_workers[job_id] = task

    async def _clean_finished_workers(self):
        """Remove completed worker tasks."""
        finished = [jid for jid, task in self.active_workers.items() if task.done()]
        for jid in finished:
            del self.active_workers[jid]
            self.stop_signals.pop(jid, None)
            self.otp_events.pop(jid, None)
            self.otp_values.pop(jid, None)

    async def _run_job_worker(
        self, job_id: int, job: dict, stop_event: asyncio.Event, otp_event: asyncio.Event
    ):
        """Run a single monitoring job using Playwright."""
        log = logger.bind(job_id=job_id)
        log.info("Worker started")

        browser: Optional[Browser] = None
        try:
            browser = await self.playwright.chromium.launch(
                headless=os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="es-ES",
            )
            page = await context.new_page()

            await self._update_job_status(job_id, "searching")
            await self._log(job_id, "info", "playwright", f"Worker started for job {job_id}")

            consecutive_errors = 0
            no_slots_count = 0
            check_count = 0

            while not stop_event.is_set():
                try:
                    result = await self._check_availability(page, job, job_id, otp_event)

                    check_count += 1
                    await self._update_check_count(job_id, check_count)
                    consecutive_errors = 0

                    if result == "found":
                        log.info("Appointment slots found!")
                        await self._update_job_status(job_id, "found")
                        break
                    elif result == "no_slots":
                        no_slots_count += 1
                        log.debug("No slots available", count=no_slots_count)
                    elif result == "stopped":
                        break

                    # Adaptive polling
                    interval = self._calculate_interval(no_slots_count, consecutive_errors)
                    log.debug("Sleeping before next check", seconds=interval)
                    await asyncio.sleep(interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    consecutive_errors += 1
                    log.warning("Check error", error=str(e), consecutive=consecutive_errors)
                    await self._log(job_id, "error", "playwright", f"Check error: {e}")
                    await self._update_error(job_id, str(e))

                    if consecutive_errors >= 10:
                        log.error("Too many consecutive errors, stopping worker")
                        await self._update_job_status(job_id, "error")
                        break

                    # Exponential backoff
                    backoff = min(300, 2 ** consecutive_errors + random.uniform(0, 10))
                    await asyncio.sleep(backoff)

        except Exception as e:
            log.error("Worker fatal error", error=str(e))
            await self._update_job_status(job_id, "error")
        finally:
            if browser:
                await browser.close()
            log.info("Worker finished")

    def _calculate_interval(self, no_slots_count: int, error_count: int) -> float:
        """
        Adaptive polling interval with jitter.
        High-activity mode after many empty checks.
        """
        poll_normal_min = int(os.environ.get("POLL_INTERVAL_NORMAL_MIN", 30))
        poll_normal_max = int(os.environ.get("POLL_INTERVAL_NORMAL_MAX", 60))
        poll_high_min = int(os.environ.get("POLL_INTERVAL_HIGH_MIN", 10))
        poll_high_max = int(os.environ.get("POLL_INTERVAL_HIGH_MAX", 25))

        # After 50 no-slot checks, use high activity mode
        if no_slots_count > 0 and no_slots_count % 50 == 0:
            base = random.uniform(poll_high_min, poll_high_max)
        else:
            base = random.uniform(poll_normal_min, poll_normal_max)

        # Add jitter
        jitter = random.uniform(-2, 2)
        return max(5, base + jitter)

    async def _check_availability(
        self, page: Page, job: dict, job_id: int, otp_event: asyncio.Event
    ) -> str:
        """
        Navigate the ICP form and check for appointment slots.
        Returns: 'found' | 'no_slots' | 'stopped' | 'otp'
        """
        timeout = int(os.environ.get("PLAYWRIGHT_TIMEOUT", 30000))

        # Navigate to ICP
        await page.goto(ICP_BASE_URL, wait_until="domcontentloaded", timeout=timeout)

        # Check if we're stopped
        if await self._is_stopped(job_id):
            return "stopped"

        # Select province
        province_code = job.get("province_code") or job.get("province_name", "")
        await self._select_province(page, province_code, timeout)

        # Click accept/continue
        await self._click_button_if_exists(page, ["#btnAceptar", "#btnEntrar", "input[type=submit]"])

        await page.wait_for_load_state("domcontentloaded", timeout=timeout)

        # Check for OTP page
        if await self._is_otp_page(page):
            await self._handle_otp(page, job_id, otp_event)
            return "no_slots"  # Continue after OTP

        # Select tramite
        tramite_code = job.get("tramite_code", "")
        await self._select_tramite(page, tramite_code, timeout)
        await self._click_button_if_exists(page, ["#btnAceptar", "input[type=submit][value='Aceptar']"])

        await page.wait_for_load_state("domcontentloaded", timeout=timeout)

        # Check for "no hay citas"
        page_text = await page.inner_text("body")
        if "No hay citas disponibles" in page_text or "no hay citas" in page_text.lower():
            await self._log(job_id, "debug", "playwright", "No slots: 'No hay citas disponibles'")
            return "no_slots"

        # Look for appointment calendar / available slots
        slot_indicators = [
            ".cita-disponible",
            ".slot-available",
            "td.available",
            "[class*='disponib']",
            "a[href*='cita']",
        ]
        for selector in slot_indicators:
            elements = await page.query_selector_all(selector)
            if elements:
                screenshot_path = await self._take_screenshot(page, job_id)
                await self._notify_found(job_id, job, screenshot_path)
                return "found"

        # Check hidden DOM changes (calendar with dates)
        calendar_elements = await page.query_selector_all("table.calendario td:not(.bloqueado)")
        if calendar_elements:
            screenshot_path = await self._take_screenshot(page, job_id)
            await self._notify_found(job_id, job, screenshot_path)
            return "found"

        return "no_slots"

    async def _is_otp_page(self, page: Page) -> bool:
        """Detect if current page requires OTP."""
        text = await page.inner_text("body")
        otp_keywords = ["otp", "código", "contraseña de un solo uso", "verificación"]
        return any(kw in text.lower() for kw in otp_keywords)

    async def _handle_otp(self, page: Page, job_id: int, otp_event: asyncio.Event):
        """
        Pause worker and wait for admin to provide OTP.
        """
        logger.warning("OTP page detected", job_id=job_id)
        screenshot_path = await self._take_screenshot(page, job_id, prefix="otp")

        # Create OTP request via backend
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_URL}/api/otp/internal/create",
                    json={
                        "job_id": job_id,
                        "screenshot_path": str(screenshot_path),
                        "context_data": json.dumps({"url": page.url}),
                    },
                    timeout=10,
                )
                otp_request = resp.json()
                otp_id = otp_request.get("id")
        except Exception as e:
            logger.error("Failed to create OTP request", error=str(e))
            return

        # Wait for OTP to be resolved (max 5 minutes)
        await self._update_job_status(job_id, "paused")

        # Poll Redis/backend for OTP resolution
        deadline = asyncio.get_event_loop().time() + 300  # 5 min
        otp_value = None
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{BACKEND_URL}/api/otp/{otp_id}",
                        timeout=5,
                    )
                    otp_data = resp.json()
                    if otp_data.get("status") == "resolved":
                        otp_value = otp_data.get("otp_value")
                        break
            except Exception:
                pass
            await asyncio.sleep(3)

        await self._update_job_status(job_id, "searching")

        if otp_value:
            # Enter OTP in page
            otp_input = await page.query_selector("input[type=text][name*='otp'], input[type=number]")
            if otp_input:
                await otp_input.fill(otp_value)
                await self._click_button_if_exists(page, ["input[type=submit]", "button[type=submit]"])
                await page.wait_for_load_state("domcontentloaded", timeout=30000)

    async def _select_province(self, page: Page, province_code: str, timeout: int):
        """Select province in the dropdown."""
        selectors = ["#form", "select[name='provincia']", "#provincia"]
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    await page.select_option(sel, value=province_code, timeout=timeout)
                    return
            except Exception:
                continue

    async def _select_tramite(self, page: Page, tramite_code: str, timeout: int):
        """Select tramite in the dropdown."""
        selectors = ["select[name='tramite']", "#tramite", "select"]
        for sel in selectors:
            try:
                await page.select_option(sel, value=tramite_code, timeout=5000)
                return
            except Exception:
                continue

    async def _click_button_if_exists(self, page: Page, selectors: list):
        """Click the first matching button."""
        for sel in selectors:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    return
            except Exception:
                continue

    async def _take_screenshot(self, page: Page, job_id: int, prefix: str = "slot") -> str:
        """Take and save a screenshot."""
        ts = int(time.time())
        filename = f"{prefix}_{job_id}_{ts}.png"
        path = SCREENSHOTS_DIR / filename
        await page.screenshot(path=str(path), full_page=True)
        return str(path)

    async def _notify_found(self, job_id: int, job: dict, screenshot_path: str):
        """Notify backend that a slot was found."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{BACKEND_URL}/api/jobs/internal/found",
                    json={
                        "job_id": job_id,
                        "screenshot_path": screenshot_path,
                    },
                    timeout=10,
                )
        except Exception as e:
            logger.error("Failed to notify found", error=str(e))

    async def _update_job_status(self, job_id: int, status: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{BACKEND_URL}/api/jobs/internal/{job_id}/status",
                    json={"status": status},
                    timeout=5,
                )
        except Exception:
            pass

    async def _update_check_count(self, job_id: int, count: int):
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{BACKEND_URL}/api/jobs/internal/{job_id}/check",
                    json={"check_count": count},
                    timeout=5,
                )
        except Exception:
            pass

    async def _update_error(self, job_id: int, error: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{BACKEND_URL}/api/jobs/internal/{job_id}/error",
                    json={"error_message": error},
                    timeout=5,
                )
        except Exception:
            pass

    async def _log(self, job_id: int, level: str, source: str, message: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{BACKEND_URL}/api/logs/internal",
                    json={"job_id": job_id, "level": level, "source": source, "message": message},
                    timeout=5,
                )
        except Exception:
            pass

    async def _is_stopped(self, job_id: int) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{BACKEND_URL}/api/jobs/{job_id}", timeout=5)
                job = resp.json()
                return job.get("status") in ("stopped", "found")
        except Exception:
            return False
