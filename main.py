#!/usr/bin/env python3
"""
main.py
Entry point for the CMPPort PPTX generation workflow.

Usage:
    python main.py

Workflow:
    1. Check if data/projects.json exists; if not, run extract-site-data.py
    2. Launch interactive CLI (from generate-pptx.py)
    3. Route selection to appropriate PPTX generator
    4. Save output to output/<presentation-name>_<timestamp>.pptx
    5. Print file path to user
"""

import importlib.util
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "projects.json"
OUTPUT_DIR = BASE_DIR / "output"


# ---------------------------------------------------------------------------
# Import helper for hyphenated module filenames
# ---------------------------------------------------------------------------

def _import_from_path(module_name: str, file_path: Path):
    """Load a Python module from an arbitrary file path."""
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Step 1: Ensure data/projects.json exists
# ---------------------------------------------------------------------------

def ensure_data():
    if DATA_FILE.is_file():
        print(f"[main] Data file found: {DATA_FILE}")
        return

    print("[main] data/projects.json not found — running extract-site-data.py ...")
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "extract-site-data.py")],
        check=False,
    )
    if result.returncode != 0:
        print("[main] ERROR: Data extraction failed. Cannot continue.", file=sys.stderr)
        sys.exit(1)

    if not DATA_FILE.is_file():
        print("[main] ERROR: extract-site-data.py ran but data/projects.json was not created.",
              file=sys.stderr)
        sys.exit(1)

    print(f"[main] Extraction complete: {DATA_FILE}")


# ---------------------------------------------------------------------------
# Step 2: Interactive CLI
# ---------------------------------------------------------------------------

def run_interactive_cli() -> dict:
    cli_module = _import_from_path(
        "generate_pptx_cli",
        BASE_DIR / "generate-pptx.py",
    )
    return cli_module.run_cli()


# ---------------------------------------------------------------------------
# Step 3 + 4: Route to generator and save
# ---------------------------------------------------------------------------

def generate_presentation(selection: dict) -> str:
    ptype = selection.get("presentation_type", "portfolio")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if ptype == "portfolio":
        from pptx_portfolio_generator import generate_portfolio_pptx
        output_path = str(OUTPUT_DIR / f"portfolio_{timestamp}.pptx")
        return generate_portfolio_pptx(selection, output_path)

    elif ptype == "team":
        from pptx_team_generator import generate_team_pptx
        output_path = str(OUTPUT_DIR / f"team_profile_{timestamp}.pptx")
        return generate_team_pptx(selection, output_path)

    elif ptype == "annual":
        from pptx_annual_generator import generate_annual_pptx
        output_path = str(OUTPUT_DIR / f"annual_report_{timestamp}.pptx")
        return generate_annual_pptx(selection, output_path)

    else:
        print(f"[main] ERROR: Unknown presentation type '{ptype}'.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> str:
    # 1. Data check / extraction
    ensure_data()

    # 2. Interactive CLI
    try:
        selection = run_interactive_cli()
    except KeyboardInterrupt:
        print("\n\n[main] Cancelled by user.")
        sys.exit(0)

    # 3 + 4. Generate and save
    print("\n[main] Generating presentation ...")
    try:
        file_path = generate_presentation(selection)
    except Exception as exc:
        print(f"\n[main] ERROR: Generation failed — {exc}", file=sys.stderr)
        sys.exit(1)

    # 5. Return path to user
    print(f"\n[main] Presentation saved to: {file_path}")
    return file_path


if __name__ == "__main__":
    main()
