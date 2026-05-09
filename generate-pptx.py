#!/usr/bin/env python3
"""
generate-pptx.py
Interactive CLI for CMPPort presentation generation.
Prompts the user to configure a PowerPoint presentation,
validates selections against data/projects.json, and returns
a structured selection object.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "projects.json")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> dict:
    if not os.path.isfile(DATA_FILE):
        print(f"ERROR: Cannot find {DATA_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

SEPARATOR = "-" * 60


def banner(title: str) -> None:
    print()
    print(SEPARATOR)
    print(f"  {title}")
    print(SEPARATOR)


def print_numbered_list(items: list, label_fn=None) -> None:
    for i, item in enumerate(items, 1):
        label = label_fn(item) if label_fn else str(item)
        print(f"  {i:>2}. {label}")


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def prompt_choice(prompt: str, choices: list, default: int = 1) -> int:
    """
    Prompt user to pick a single number from 1..len(choices).
    Returns the 0-based index of the chosen item.
    """
    while True:
        try:
            raw = input(f"{prompt} [1-{len(choices)}, default={default}]: ").strip()
            if raw == "":
                return default - 1
            val = int(raw)
            if 1 <= val <= len(choices):
                return val - 1
            print(f"  Please enter a number between 1 and {len(choices)}.")
        except (ValueError, EOFError):
            print("  Invalid input. Please enter a number.")


def prompt_multiselect(prompt: str, items: list, required: bool = True) -> list:
    """
    Prompt user to enter comma-separated numbers to select multiple items.
    Returns list of selected 0-based indices.
    Supports 'all' to select everything.
    """
    print(f"\n{prompt}")
    print("  Enter numbers separated by commas (e.g. 1,3,5), or 'all' to select all.")
    while True:
        try:
            raw = input("  Your selection: ").strip()
        except EOFError:
            raw = ""

        if raw.lower() == "all":
            return list(range(len(items)))

        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts:
            if required:
                print("  Selection cannot be empty. Please select at least one item.")
                continue
            else:
                return []

        indices = []
        valid = True
        for part in parts:
            try:
                val = int(part)
                if 1 <= val <= len(items):
                    idx = val - 1
                    if idx not in indices:
                        indices.append(idx)
                else:
                    print(f"  '{part}' is out of range (1-{len(items)}). Try again.")
                    valid = False
                    break
            except ValueError:
                print(f"  '{part}' is not a valid number. Try again.")
                valid = False
                break

        if valid and (indices or not required):
            return indices


def prompt_text(prompt: str, required: bool = True, default: str = "") -> str:
    """Prompt for free text input. Returns stripped string."""
    hint = f" [default: {default}]" if default else ""
    while True:
        try:
            raw = input(f"{prompt}{hint}: ").strip()
        except EOFError:
            raw = ""

        if raw == "" and default:
            return default
        if raw == "" and required:
            print("  This field is required. Please enter a value.")
            continue
        return raw


# ---------------------------------------------------------------------------
# Step: Presentation type
# ---------------------------------------------------------------------------

PRESENTATION_TYPES = [
    ("portfolio", "Portfolio / Showcase"),
    ("team",      "Team Profile"),
    ("annual",    "Annual Report"),
]


def select_presentation_type() -> str:
    banner("Step 1: Presentation Type")
    print_numbered_list(PRESENTATION_TYPES, label_fn=lambda x: x[1])
    idx = prompt_choice("Select presentation type", PRESENTATION_TYPES)
    chosen_key, chosen_label = PRESENTATION_TYPES[idx]
    print(f"  Selected: {chosen_label}")
    return chosen_key


# ---------------------------------------------------------------------------
# Step: Project selection
# ---------------------------------------------------------------------------

def select_projects(projects: list, ptype: str) -> list:
    # Team Profile allows skipping project selection
    if ptype == "team":
        banner("Step 2: Project Selection (optional for Team Profile)")
        print("  For a Team Profile presentation, project selection is optional.")
        try:
            skip = input("  Skip project selection? [y/N]: ").strip().lower()
        except EOFError:
            skip = "n"
        if skip == "y":
            return []
    else:
        banner("Step 2: Project Selection")

    print_numbered_list(
        projects,
        label_fn=lambda p: f"{p['id']:16s}  {p['name']}  ({p['year']})  [{p['category']}]"
    )

    required = ptype != "team"
    indices = prompt_multiselect(
        "Select projects to include:",
        projects,
        required=required,
    )
    selected = [projects[i]["id"] for i in indices]
    print(f"  Selected {len(selected)} project(s): {', '.join(selected) if selected else '(none)'}")
    return selected


# ---------------------------------------------------------------------------
# Step: Team member selection
# ---------------------------------------------------------------------------

def select_team_members(team: list, ptype: str) -> list:
    # Portfolio and Annual Report allow skipping team selection
    if ptype in ("portfolio", "annual"):
        banner("Step 3: Team Member Selection (optional)")
        print("  Team member inclusion is optional for this presentation type.")
        try:
            skip = input("  Skip team selection? [y/N]: ").strip().lower()
        except EOFError:
            skip = "n"
        if skip == "y":
            return []
    else:
        banner("Step 3: Team Member Selection")

    print_numbered_list(
        team,
        label_fn=lambda m: f"{m['name']}  —  {m['role']}"
    )

    required = ptype == "team"
    indices = prompt_multiselect(
        "Select team members to include:",
        team,
        required=required,
    )
    selected = [team[i]["name"] for i in indices]
    print(f"  Selected {len(selected)} member(s): {', '.join(selected) if selected else '(none)'}")
    return selected


# ---------------------------------------------------------------------------
# Step: Title and subtitle
# ---------------------------------------------------------------------------

def select_title_and_subtitle(ptype: str, company_name: str) -> tuple:
    banner("Step 4: Presentation Title & Subtitle")

    type_defaults = {
        "portfolio": ("Project Portfolio 2026", f"{company_name} – Selected Works"),
        "team":      ("Our Team", f"{company_name}"),
        "annual":    ("Annual Report 2026", f"{company_name}"),
    }
    default_title, default_subtitle = type_defaults.get(ptype, ("Presentation", company_name))

    title = prompt_text("  Presentation title", required=True, default=default_title)
    subtitle = prompt_text("  Subtitle / client name", required=False, default=default_subtitle)
    return title, subtitle


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_selection(selection: dict, valid_project_ids: set, valid_member_names: set) -> list:
    errors = []

    ptype = selection.get("presentation_type")
    projects = selection.get("projects", [])
    members = selection.get("team_members", [])

    # Validate project IDs
    for pid in projects:
        if pid not in valid_project_ids:
            errors.append(f"Unknown project ID: '{pid}'")

    # Validate team member names
    for name in members:
        if name not in valid_member_names:
            errors.append(f"Unknown team member: '{name}'")

    # Enforce non-empty rules
    if ptype in ("portfolio", "annual") and not projects:
        errors.append("At least one project must be selected for Portfolio / Annual Report.")

    if ptype == "team" and not members:
        errors.append("At least one team member must be selected for Team Profile.")

    if not selection.get("title", "").strip():
        errors.append("Presentation title cannot be empty.")

    return errors


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def run_cli() -> dict:
    print()
    print("=" * 60)
    print("  CMP Management Asia — Presentation Generator")
    print("=" * 60)
    print("  Follow the prompts to configure your presentation.")
    print("  Press Ctrl+C at any time to cancel.")
    print()

    data = load_data()
    projects = data.get("projects", [])
    team = data.get("team", [])
    company = data.get("company", {})
    company_name = company.get("name", "CMP Management Asia")

    valid_project_ids = {p["id"] for p in projects}
    valid_member_names = {m["name"] for m in team}

    # --- Step 1 ---
    ptype = select_presentation_type()

    # --- Step 2 ---
    selected_projects = select_projects(projects, ptype)

    # --- Step 3 ---
    selected_members = select_team_members(team, ptype)

    # --- Step 4 ---
    title, subtitle = select_title_and_subtitle(ptype, company_name)

    # --- Assemble ---
    selection = {
        "presentation_type": ptype,
        "projects": selected_projects,
        "team_members": selected_members,
        "title": title,
        "subtitle": subtitle,
    }

    # --- Validate ---
    errors = validate_selection(selection, valid_project_ids, valid_member_names)
    if errors:
        print()
        print("VALIDATION ERRORS:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # --- Summary ---
    banner("Summary")
    ptype_label = next((label for key, label in PRESENTATION_TYPES if key == ptype), ptype)
    print(f"  Type     : {ptype_label}")
    print(f"  Projects : {', '.join(selection['projects']) if selection['projects'] else '(none)'}")
    print(f"  Team     : {', '.join(selection['team_members']) if selection['team_members'] else '(none)'}")
    print(f"  Title    : {selection['title']}")
    print(f"  Subtitle : {selection['subtitle']}")
    print()

    try:
        confirm = input("  Proceed with this configuration? [Y/n]: ").strip().lower()
    except EOFError:
        confirm = "y"
    if confirm == "n":
        print("  Cancelled.")
        sys.exit(0)

    return selection


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        result = run_cli()
        print()
        print("Configuration complete. Selection object:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        print("Ready for PPTX generation.")
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
