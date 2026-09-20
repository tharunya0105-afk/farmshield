# -*- coding: utf-8 -*-
"""Capture FarmShield app screenshots for the hackathon deck (honest prototype labels included)."""
import asyncio, os
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
OUT = "shots"
os.makedirs(OUT, exist_ok=True)

SHOTS = [
    # (name, path, width, height, settle_seconds)
    ("landing",       "/", 1366, 850, 3),
    ("farmer_home",   "/?mode=farmer", 400, 820, 4),
    ("farmer_tamil",  "/?mode=farmer&lang=ta", 400, 820, 4),
    ("farmer_alerts", "/?mode=farmer", 400, 820, 4),
    ("expert_dash",   "/?mode=expert", 1366, 830, 5),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for name, path, w, h, settle in SHOTS:
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.goto(BASE + path, wait_until="networkidle")
            await asyncio.sleep(settle)
            if name == "farmer_alerts":
                # tap the Alerts tab in the bottom nav
                try:
                    await page.click("nav button:nth-child(3)", timeout=3000)
                    await asyncio.sleep(1.5)
                except Exception as e:
                    print("alerts tab click failed:", e)
            await page.screenshot(path=f"{OUT}/{name}.png")
            print("captured", name)
            await page.close()
        await browser.close()

asyncio.run(main())
