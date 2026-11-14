"""Capture six final app panels per farm from local Streamlit."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"


def local_port():
    with socket.socket() as listener:
        listener.bind((HOST, 0))
        return listener.getsockname()[1]


def wait_for_streamlit(url, process):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with urlopen(f"{url}/_stcore/health", timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError):
            time.sleep(0.25)
    raise RuntimeError("Local Streamlit server did not become ready")


def capture(url, destination, channel=None):
    farms = json.loads((ROOT / "data/processed/app_settings.json").read_text())["farms"]
    destination.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel)
        context = browser.new_context(viewport={"width": 1450, "height": 1000}, device_scale_factor=1)
        # Reject external HTTP resources to verify that the browser demo is self-contained.
        context.route("**/*", lambda route: route.continue_() if urlsplit(route.request.url).hostname == HOST
                      else route.abort())
        for farm in farms:
            name, farm_id = farm["name"], farm["farm_id"]
            page = context.new_page()
            page.goto(url)
            picker = page.get_by_role("combobox", name="Choose an illustrative farm")
            expect(picker).to_be_visible()
            if picker.input_value() != name:
                picker.click()
                page.get_by_role("option", name=name, exact=True).click()
            climate = page.locator(".st-key-climate_assessment")
            expect(climate.get_by_text(name, exact=True)).to_be_visible()
            comparison = page.locator(".st-key-strategy_comparison")
            expect(comparison.get_by_text(name, exact=True)).to_be_visible()
            for panel, locator in (("climate", climate), ("comparison", comparison)):
                expect(locator.locator(".js-plotly-plot:visible").first).to_be_visible()
                locator.screenshot(path=destination / f"{farm_id}_{panel}.png", animations="disabled")
            validation = page.locator(".st-key-historical_validation")
            expect(validation.get_by_text("Validation · historical back-test")).to_be_visible()
            expect(validation.locator(".js-plotly-plot:visible").first).to_be_visible()
            validation.screenshot(path=destination / f"{farm_id}_validation.png", animations="disabled")
            robustness = page.locator(".st-key-climate_stress_test")
            expect(robustness.get_by_text("Robustness check")).to_be_visible()
            expect(robustness.locator(".js-plotly-plot:visible").first).to_be_visible()
            robustness.screenshot(path=destination / f"{farm_id}_robustness.png", animations="disabled")
            scenario = comparison.get_by_role("combobox", name="Scenario")
            scenario.click()
            page.get_by_role("option", name="Warmer and drier", exact=True).click()
            uncertainty = page.locator(".st-key-uncertainty_baseline")
            expect(uncertainty.get_by_text(f"{name} · Existing rotation · Warmer and drier", exact=True)).to_be_visible()
            expect(uncertainty.get_by_text("Wins in", exact=False)).to_be_visible()
            uncertainty.screenshot(path=destination / f"{farm_id}_uncertainty.png", animations="disabled")
            grade_details = uncertainty.get_by_text("Evidence grade shares and input sources")
            expect(grade_details).to_be_visible()
            grade_details.click()
            expect(uncertainty.get_by_text("nasa measured", exact=False).first).to_be_visible()
            uncertainty.screenshot(path=destination / f"{farm_id}_evidence.png", animations="disabled")
            page.close()
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/screenshots")
    parser.add_argument("--channel", choices=["chrome", "msedge"], help="Use an installed browser channel")
    args = parser.parse_args()
    port = local_port()
    url = f"http://{HOST}:{port}"
    command = [sys.executable, "-m", "streamlit", "run", str(ROOT / "app/main.py"),
               "--server.address", HOST, "--server.port", str(port), "--server.headless", "true",
               "--server.fileWatcherType", "none"]
    with tempfile.TemporaryFile(mode="w+b") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"})
        try:
            wait_for_streamlit(url, process)
            capture(url, args.output, args.channel)
        except Exception:
            log.seek(0)
            print(log.read().decode(errors="replace"), file=sys.stderr)
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
