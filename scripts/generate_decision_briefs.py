"""Export all reference briefs, with optional local Chromium printing."""

import argparse
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.decision_brief import BRIEFS, brief_filename, reference_inputs, render_brief, repository_version


def write_html(destination, generated_on, commit):
    data = ROOT / "data/processed"
    settings = json.loads((data / "app_settings.json").read_text(encoding="utf-8"))

    def load(farm_id, prefix):
        return json.loads((data / f"{prefix}_{farm_id}.json").read_text(encoding="utf-8"))

    for farm in settings["farms"]:
        inputs = tuple(reference_inputs(load, farm["farm_id"]))
        for preset in settings["weights_presets"]["presets"]:
            stem = brief_filename(farm["farm_id"], preset)
            path = destination / f"{stem}.html"
            path.write_text(render_brief(farm, preset, *inputs, generated_on=generated_on, commit=commit),
                            encoding="utf-8")
            yield path


def print_pdfs(files, channel, paper):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        with playwright.chromium.launch(channel=channel) as browser:
            context = browser.new_context(offline=True)
            # The document is supplied from memory. Block all attempted external resources.
            context.route("**/*", lambda route: route.abort())
            page = context.new_page()
            for path in files:
                page.set_content(path.read_text(encoding="utf-8"))
                page.pdf(path=path.with_suffix(".pdf"), format=paper, print_background=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BRIEFS)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--pdf", action="store_true", help="Print each HTML file with local Playwright Chromium")
    parser.add_argument("--channel", choices=["chrome", "msedge"])
    parser.add_argument("--paper", choices=["Letter", "A4"], default="Letter")
    args = parser.parse_args()
    commit = repository_version()
    if commit == "Unavailable":
        parser.error("A Git checkout or bundled source commit is required")
    args.output.mkdir(parents=True, exist_ok=True)
    files = list(write_html(args.output, args.date, commit))
    if args.pdf:
        print_pdfs(files, args.channel, args.paper)
        release = {"source_commit": commit, "generated_on": args.date.isoformat(), "pdf_paper": args.paper}
        (args.output / "release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(files)} HTML briefs" + (f" and {len(files)} {args.paper} PDFs" if args.pdf else ""))


if __name__ == "__main__":
    main()
