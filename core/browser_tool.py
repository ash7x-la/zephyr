import os
import asyncio
try:
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from core.logger import Logger

class BrowserTool:
    def __init__(self):
        self.is_termux = os.path.exists("/data/data/com.termux")
        self.browser_path = "/data/data/com.termux/files/usr/bin/chromium" if self.is_termux else None

    async def test_url(self, url: str, actions: list = None, get_html: bool = False, html_selector: str = "body", **kwargs):
        """
        Membuka URL di browser (Playwright) dan mengeksekusi serangkaian aksi (click, fill, dsb).
        Mengambil status DOM serta log konsol untuk debugging otonom.
        Serta mendukung pemotretan (screenshot) dan ekstraksi HTML (Copy UI).
        """
        results = {
            "url": url,
            "status": "fail",
            "console_logs": [],
            "page_content_summary": "",
            "actions_performed": [],
            "screenshot_path": "",
            "html_data": "",
            "error": None
        }

        if not PLAYWRIGHT_AVAILABLE:
            error_msg = "Playwright/Stealth tidak terinstall. Jalankan 'pip install playwright playwright-stealth' jika di Linux/WSL."
            results["status"] = "error"
            results["error"] = error_msg
            results["message"] = error_msg
            return results

        try:
            async with async_playwright() as p:
                # Pilih browser engine
                browser_args = {}
                if self.browser_path and os.path.exists(self.browser_path):
                    browser_args["executable_path"] = self.browser_path
                
                Logger.debug(f"Launching browser (Termux: {self.is_termux})...")
                browser = await p.chromium.launch(headless=True, **browser_args)
                context = await browser.new_context(viewport={'width': 1280, 'height': 720})
                page = await context.new_page()
                
                # Aktifkan stealth mode (Evasion) via v2.x API
                stealth = Stealth()
                await stealth.apply_stealth_async(page)

                # Capture console logs
                page.on("console", lambda msg: results["console_logs"].append(f"[{msg.type}] {msg.text}"))
                page.on("pageerror", lambda err: results["console_logs"].append(f"[ERROR] {err.message}"))

                # Navigate (Faster with domcontentloaded)
                Logger.debug(f"Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Execute actions if provided
                if actions:
                    for action in actions:
                        action_type = action.get("type")
                        selector = action.get("selector")
                        value = action.get("value", "")
                        
                        Logger.debug(f"Action: {action_type} on {selector}")
                        try:
                            if action_type == "click":
                                await page.click(selector, timeout=5000)
                            elif action_type == "fill":
                                await page.fill(selector, value, timeout=5000)
                            elif action_type == "press":
                                await page.press(selector, value, timeout=5000)
                            elif action_type == "wait":
                                await page.wait_for_selector(selector, timeout=5000)
                            
                            results["actions_performed"].append(f"OK: {action_type} on {selector}")
                        except Exception as ae:
                            results["actions_performed"].append(f"FAIL: {action_type} on {selector} ({str(ae)})")
                            break # Berhenti jika ada aksi yang gagal

                # Final page state analysis
                title = await page.title()
                content = await page.evaluate("() => document.body.innerText.substring(0, 1000)")
                node_count = await page.evaluate("() => document.querySelectorAll('*').length")

                # Take screenshot for visual verification
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"screenshot_{timestamp}.png"
                screenshot_dir = os.path.join("memory", "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
                await page.screenshot(path=screenshot_path)

                # Optional HTML extraction (Copy UI)
                html_data = ""
                if get_html:
                    try:
                        html_data = await page.inner_html(html_selector, timeout=5000)
                    except Exception as he:
                        html_data = f"Error extracting HTML from {html_selector}: {str(he)}"

                results["status"] = "success"
                results["page_content_summary"] = f"Title: {title}\nNodes: {node_count}\nContent Sample: {content[:200]}..."
                results["screenshot_path"] = screenshot_path
                results["html_data"] = html_data
                
                if node_count < 5:
                    results["status"] = "blank_page_detected"

                # Build 'message' for Orchestrator compatibility
                error_count = len([l for l in results["console_logs"] if "[error]" in l.lower()])
                results["message"] = f"Title: {title} | DOM Nodes: {node_count} | Console Errors: {error_count} | Screenshot: {screenshot_path}"
                if results["actions_performed"]:
                    results["message"] += f" | Actions: {len(results['actions_performed'])}"

                await browser.close()
                Logger.debug(f"Browser interaction finished: {results['status']}")
                
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["message"] = f"Browser Error: {str(e)}"
            Logger.error(f"Browser Tool Error: {str(e)}")

        return results

# Singleton instance
browser_tool_instance = BrowserTool()

async def run_browser_test(url: str, actions: list = None, get_html: bool = False, html_selector: str = "body", **kwargs):
    return await browser_tool_instance.test_url(url, actions, get_html, html_selector, **kwargs)
