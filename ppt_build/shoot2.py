# -*- coding: utf-8 -*-
"""Capture interactive FarmShield screens: completed demo, detection result, expert map."""
import asyncio, os
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
OUT = "shots"
os.makedirs(OUT, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # 1) Live demo run to completion (timeline fully checked)
        page = await browser.new_page(viewport={"width": 480, "height": 900})
        await page.goto(BASE + "/?mode=demo", wait_until="networkidle")
        await asyncio.sleep(2.5)
        await page.click("text=Start Demo")
        print("demo started, waiting 24s...")
        await asyncio.sleep(24)
        await page.screenshot(path=f"{OUT}/demo_done.png", full_page=False)
        print("captured demo_done")
        await page.close()

        # 2) Farmer detection result (scan -> result)
        page = await browser.new_page(viewport={"width": 400, "height": 820})
        await page.goto(BASE + "/?mode=farmer", wait_until="networkidle")
        await asyncio.sleep(3)
        await page.click("text=Check Crop")
        await asyncio.sleep(4.5)  # scan + analyze
        await page.screenshot(path=f"{OUT}/farmer_result.png")
        print("captured farmer_result")
        await page.close()

        # 3) Expert field map page
        page = await browser.new_page(viewport={"width": 1366, "height": 830})
        await page.goto(BASE + "/?mode=expert", wait_until="networkidle")
        await asyncio.sleep(4)
        await page.click("text=Field Map")
        await asyncio.sleep(4)  # tiles
        await page.screenshot(path=f"{OUT}/expert_map.png")
        print("captured expert_map")
        await page.close()

        await browser.close()

asyncio.run(main())
