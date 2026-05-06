"""
CitaMonitor Worker
Playwright monitoring engine — polls for appointment availability.
"""
import asyncio
import os
import structlog
from worker.monitor import MonitoringEngine

logger = structlog.get_logger()


async def main():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    logger.info("Starting CitaMonitor Worker")
    engine = MonitoringEngine()
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
