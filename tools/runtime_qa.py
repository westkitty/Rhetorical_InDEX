#!/usr/bin/env python3
from __future__ import annotations
import contextlib
import http.server
import json
import socket
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "apps" / "web" / "dist"
SCREEN = ROOT / "qa" / "screens"
REPORT = ROOT / "qa" / "runtime-results.json"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def serve(directory: Path):
    class Handler(QuietHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)
    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def assert_true(results, name, condition, detail=""):
    results.append({"name": name, "pass": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail}")


def run_context(browser, html, width, height, mobile=False, suffix="desktop"):
    results = []
    console_errors = []
    requests = []
    context = browser.new_context(viewport={"width": width, "height": height}, is_mobile=mobile, has_touch=mobile)
    page = context.new_page()
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("request", lambda req: requests.append(req.url))
    page.set_content(html, wait_until="load")

    assert_true(results, f"{suffix}: scanner visible", page.locator("#scannerView.active").count() == 1)
    assert_true(results, f"{suffix}: one semantic article", page.locator("#articleBase").count() == 1)
    assert_true(results, f"{suffix}: overlay aria hidden", page.locator("#articleOverlay[aria-hidden=true]").count() == 1)
    aligned = page.locator("#articleSurface").get_attribute("data-overlay-aligned")
    delta = page.locator("#articleSurface").get_attribute("data-overlay-max-delta")
    assert_true(results, f"{suffix}: overlay geometry aligned", aligned == "true", f"delta={delta}")

    if suffix == "desktop":
        first = page.locator("#articleBase .base-mark").first
        box = first.bounding_box()
        assert_true(results, "desktop: first finding has geometry", bool(box), str(box))
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(80)
            assert_true(results, "desktop: lens readout appears over finding", page.locator("#lensReadout:not([hidden])").count() == 1)
        page.locator("#revealToggle").click()
        assert_true(results, "desktop: Reveal All class applied", "reveal-all" in (page.locator("#articleSurface").get_attribute("class") or ""))
        page.locator("#revealToggle").click()

        row = page.locator("#findingsList .finding-row").first
        row.focus()
        page.evaluate("window.__riFocusBefore = document.activeElement?.getAttribute('data-finding')")
        row.click()
        assert_true(results, "desktop: drawer opens", page.locator("#findingDrawer.open").count() == 1)
        for _ in range(8):
            page.keyboard.press("Tab")
            inside = page.evaluate("document.getElementById('findingDrawer').contains(document.activeElement)")
            assert_true(results, "desktop: focus remains trapped", bool(inside))
        page.keyboard.press("Escape")
        restored = page.evaluate("document.activeElement?.getAttribute('data-finding') === window.__riFocusBefore")
        assert_true(results, "desktop: drawer restores focus", bool(restored))

        page.locator("#reducedMotionToggle").check()
        assert_true(results, "desktop: Reduced Motion class applied", "user-reduced-motion" in (page.locator("body").get_attribute("class") or ""))
        page.locator("#patternModeToggle").check()
        assert_true(results, "desktop: Pattern mode class applied", "pattern-mode" in (page.locator("body").get_attribute("class") or ""))

        page.locator('[data-action="open-paste"]').first.click()
        sample = "Officials refused to explain why the safeguards failed.\n\nMistakes were made during the review.\n\nCitizens face either total monitoring or digital exile.\n\nThe reckless plan was described as catastrophic."
        page.locator("#pasteText").fill(sample)
        page.locator("#runPaste").click()
        assert_true(results, "desktop: local preview banner", "LOCAL PREVIEW" in page.locator("#modeBanner").inner_text())
        assert_true(results, "desktop: local preview produces candidates", page.locator("#findingsList .finding-row").count() >= 4)
        page.locator('[data-view="compare"]').click()
        assert_true(results, "desktop: single-document Compare is unavailable", "Comparison unavailable" in page.locator("#compareView").inner_text())
        page.locator('[data-view="scanner"]').click()
        page.locator('[data-action="load-demo"]').first.click()

    if mobile:
        handle = page.locator("#touchLensHandle")
        assert_true(results, f"{suffix}: touch handle visible", handle.is_visible())
        surface = page.locator("#articleSurface")
        sbox = surface.bounding_box()
        if sbox:
            page.touchscreen.tap(sbox["x"] + min(180, sbox["width"] / 2), sbox["y"] + 340)
            page.wait_for_timeout(50)
            lens = page.evaluate("({x:parseFloat(getComputedStyle(document.getElementById('articleSurface')).getPropertyValue('--lens-x')),y:parseFloat(getComputedStyle(document.getElementById('articleSurface')).getPropertyValue('--lens-y')),r:parseFloat(getComputedStyle(document.getElementById('articleSurface')).getPropertyValue('--lens-r')),w:document.getElementById('articleSurface').clientWidth})")
            assert_true(results, f"{suffix}: lens radius-aware x bounds", lens["x"] >= lens["r"] and lens["x"] <= lens["w"] - lens["r"], json.dumps(lens))
        assert_true(results, f"{suffix}: no horizontal overflow", page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"))
        page.evaluate("window.scrollTo(0, 420)")
        page.wait_for_timeout(80)
        topbar_box = page.locator("#topbar").bounding_box()
        toolbar_box = page.locator(".scanner-toolbar").bounding_box()
        if width > 720 and topbar_box and toolbar_box:
            assert_true(results, f"{suffix}: sticky scanner clears wrapped topbar", toolbar_box["y"] >= topbar_box["y"] + topbar_box["height"] - 1, json.dumps({"topbar": topbar_box, "toolbar": toolbar_box}))
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(30)
        hbox = handle.bounding_box()
        if hbox:
            px = hbox["x"] + hbox["width"] / 2
            py = hbox["y"] + hbox["height"] / 2
            handle.dispatch_event("pointerdown", {"pointerId": 41, "pointerType": "touch", "clientX": px, "clientY": py, "bubbles": True})
            assert_true(results, f"{suffix}: pointer ownership begins", page.locator("#articleSurface").get_attribute("data-dragging") == "true")
            handle.dispatch_event("pointercancel", {"pointerId": 41, "pointerType": "touch", "clientX": px, "clientY": py, "bubbles": True})
            assert_true(results, f"{suffix}: pointercancel clears ownership", page.locator("#articleSurface").get_attribute("data-dragging") == "false" and page.locator("#articleSurface").get_attribute("data-active-pointer") == "")

    SCREEN.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREEN / f"{suffix}.png"), full_page=False)
    assert_true(results, f"{suffix}: no console errors", len(console_errors) == 0, " | ".join(console_errors))
    external = [r for r in requests if not r.startswith('data:')]
    assert_true(results, f"{suffix}: no external requests", len(external) == 0, json.dumps(external))
    context.close()
    return results


def main():
    if not (DIST / "index.html").exists():
        raise SystemExit("Build apps/web/dist/index.html before runtime QA")
    html = (DIST / "index.html").read_text()
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        all_results += run_context(browser, html, 1440, 1000, mobile=False, suffix="desktop")
        all_results += run_context(browser, html, 768, 1024, mobile=True, suffix="tablet-portrait")
        all_results += run_context(browser, html, 1024, 768, mobile=True, suffix="tablet-landscape")
        all_results += run_context(browser, html, 410, 844, mobile=True, suffix="phone")
        browser.close()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"checks": all_results, "passed": sum(1 for r in all_results if r["pass"]), "total": len(all_results)}, indent=2) + "\n")
    print(f"Runtime QA: {sum(1 for r in all_results if r['pass'])}/{len(all_results)} checks pass")

if __name__ == "__main__":
    main()
