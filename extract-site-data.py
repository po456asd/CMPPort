#!/usr/bin/env python3
"""
extract-site-data.py
Parses index.html and builds data/projects.json for CMPPort site.
"""

import json
import os
import re
from html.parser import HTMLParser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "index.html")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "projects.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_path(p: str) -> str:
    """Strip leading ./ and normalise separators."""
    p = p.strip().lstrip("./")
    return p.replace("\\", "/")


def image_exists(rel_path: str) -> bool:
    full = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    return os.path.isfile(full)


# ---------------------------------------------------------------------------
# Extract JS image arrays
# ---------------------------------------------------------------------------

def extract_js_image_arrays(html: str) -> dict:
    """
    Pull every `const <name>Images = [...]` block out of the inline JS.
    Returns { key: [list_of_paths] }
    """
    # Match both multi-line and single-line array declarations
    pattern = re.compile(
        r"const\s+(\w+Images)\s*=\s*\[(.*?)\]",
        re.DOTALL,
    )
    result = {}
    for match in pattern.finditer(html):
        var_name = match.group(1)  # e.g. "atlasImages"
        raw = match.group(2)
        # Extract all quoted strings
        paths = re.findall(r"['\"]([^'\"]+)['\"]", raw)
        # Normalise paths
        clean_paths = []
        for p in paths:
            norm = normalize_path(p)
            if norm.startswith("img/"):
                clean_paths.append(norm)
        key = var_name.replace("Images", "")  # e.g. "atlas"
        if clean_paths:
            result[key] = clean_paths
    return result


# ---------------------------------------------------------------------------
# Extract project cards from HTML
# ---------------------------------------------------------------------------

def extract_projects_html(html: str) -> list:
    """
    Extract project cards by parsing pillar-card divs in the portfolio section.
    Returns list of dicts with keys: id, name, description, category, client,
    role, start, complete.
    """
    # Find portfolio section
    port_match = re.search(r'id="portfolio"', html)
    if not port_match:
        return []

    portfolio_html = html[port_match.start():]

    # Find category groups (h3 headings)
    category_map = {}
    for cat_match in re.finditer(
        r'<h3[^>]*>(Mega-Projects|Specialized Builds|Residential &amp; Medical|Residential & Medical)</h3>(.*?)(?=<h3|</div>\s*</div>\s*</section)',
        portfolio_html,
        re.DOTALL,
    ):
        cat_label = cat_match.group(1).replace("&amp;", "&")
        cat_html = cat_match.group(2)

        # Determine category id
        if "Mega" in cat_label:
            cat_id = "mega"
        elif "Specialized" in cat_label:
            cat_id = "specialized"
        else:
            cat_id = "residential"

        # Find each onclick to map gallery key
        for onclick_match in re.finditer(r'onclick="open(\w+)Gallery\(\)"', cat_html):
            gallery_key = onclick_match.group(1)
            # lowercase first char
            key = gallery_key[0].lower() + gallery_key[1:]
            category_map[key] = cat_id

    # Now extract each project card
    projects = []

    # Pattern: pillar-card divs with onclick openXxxGallery
    card_pattern = re.compile(
        r'onclick="open(\w+)Gallery\(\)".*?<h4[^>]*>(.*?)</h4>(.*?)(?=class="pillar-card|</div>\s*</div>\s*(?:<div|</section))',
        re.DOTALL,
    )

    for m in card_pattern.finditer(portfolio_html):
        gallery_key_raw = m.group(1)
        # normalise key to match JS array names
        gallery_key = gallery_key_raw[0].lower() + gallery_key_raw[1:]

        name = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        body = m.group(3)

        # Description: first <p> with text-muted class
        desc_match = re.search(r'color: var\(--text-muted\)[^>]*>(.*?)</p>', body)
        description = ""
        if desc_match:
            description = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()

        # Client
        client = ""
        client_match = re.search(r'Client:\s*([^<]+)', body)
        if client_match:
            client = client_match.group(1).strip()

        # Role
        role = ""
        role_match = re.search(r'<strong>Role:</strong>\s*([^<]+)', body)
        if role_match:
            role = role_match.group(1).strip()

        # Start year
        year = None
        start_match = re.search(r'Project Start[^>]*>.*?(\d{4})', body)
        if start_match:
            year = int(start_match.group(1))

        # Category
        cat = category_map.get(gallery_key, "construction")

        projects.append({
            "_gallery_key": gallery_key,
            "name": name,
            "description": description,
            "category": cat,
            "client": client,
            "role": role,
            "year": year,
        })

    return projects


# ---------------------------------------------------------------------------
# Map gallery key -> project id
# ---------------------------------------------------------------------------

GALLERY_KEY_TO_ID = {
    "atlas": "atlas",
    "quarter": "quarter",
    "obk": "obk",
    "trp": "trp",
    "kbh": "kbh",
    "pryd": "pryd",
    "obkf": "obkf",
    "thaiOil": "thaiOil",
    "tempFactory": "tempFactory",
    "pierreRepair": "pierreRepair",
    "kaoyai": "kaoyai",
    "boonNak": "boonNak",
}

# Featured projects (first entry per category)
FEATURED_IDS = {"atlas", "obk", "kbh"}


# ---------------------------------------------------------------------------
# Extract team members
# ---------------------------------------------------------------------------

def extract_team(html: str) -> list:
    """
    Parse the Our Team section for name, role, and bio.
    """
    team_match = re.search(r'<h2>Our Team</h2>(.*?)</section>', html, re.DOTALL)
    if not team_match:
        return []

    section = team_match.group(1)

    members = []
    # Each member is in a pillar-card
    for card in re.finditer(r'<div class="pillar-card fade-in-stagger">(.*?)(?=<div class="pillar-card|</div>\s*</div>\s*</div>)', section, re.DOTALL):
        card_html = card.group(1)

        # Name: h3
        name_match = re.search(r'<h3[^>]*>(.*?)</h3>', card_html)
        name = re.sub(r"<[^>]+>", "", name_match.group(1)).strip() if name_match else ""

        # Role: first <p> with accent-gold and font-weight: 600
        role_match = re.search(r'font-weight: 600[^>]*>(.*?)</p>', card_html)
        role = re.sub(r"<[^>]+>", "", role_match.group(1)).strip() if role_match else ""

        # Bio: last <p> (text-muted)
        bio_match = re.search(r'color: var\(--text-muted\)[^>]*>(.*?)</p>', card_html)
        bio = re.sub(r"<[^>]+>", "", bio_match.group(1)).strip() if bio_match else ""

        if name:
            members.append({"name": name, "role": role, "bio": bio})

    return members


# ---------------------------------------------------------------------------
# Extract company info
# ---------------------------------------------------------------------------

def extract_company(html: str) -> dict:
    title_match = re.search(r"<title>([^<]+)</title>", html)
    tagline_match = re.search(r"From Vision to Guaranteed Reality[^\"<]*", html)

    name = "CMP Management Asia"
    tagline = tagline_match.group(0).strip() if tagline_match else "From Vision to Guaranteed Reality"

    return {"name": name, "tagline": tagline}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Reading {HTML_FILE} ...")
    with open(HTML_FILE, encoding="utf-8") as f:
        html = f.read()

    # --- Image arrays ---
    print("Extracting JS image arrays ...")
    image_arrays = extract_js_image_arrays(html)
    print(f"  Found image arrays: {sorted(image_arrays.keys())}")

    # --- Project cards ---
    print("Extracting project cards ...")
    cards = extract_projects_html(html)
    print(f"  Found {len(cards)} project cards")

    # --- Build project list ---
    projects = []
    # Canonical order matching PRD
    canonical_order = [
        "atlas", "quarter", "obk", "trp", "kbh", "pryd",
        "obkf", "thaiOil", "tempFactory", "pierreRepair", "kaoyai", "boonNak",
    ]

    # Build lookup from cards
    card_lookup = {c["_gallery_key"]: c for c in cards}

    for proj_id in canonical_order:
        card = card_lookup.get(proj_id, {})
        images_raw = image_arrays.get(proj_id, [])

        # Validate image paths
        validated_images = []
        missing = []
        for img in images_raw:
            if image_exists(img):
                validated_images.append(img)
            else:
                missing.append(img)

        if missing:
            print(f"  WARNING: {proj_id} has {len(missing)} missing image(s): {missing[:3]}{'...' if len(missing)>3 else ''}")

        cat_raw = card.get("category", "construction")
        if cat_raw == "mega":
            category = "commercial"
        elif cat_raw == "specialized":
            category = "construction"
        else:
            category = "residential"

        year = card.get("year")
        if year is None:
            # fallback defaults
            year_defaults = {
                "atlas": 2023, "quarter": 2024, "obk": 2019, "trp": 2023,
                "kbh": 2023, "pryd": 2025, "obkf": 2021, "thaiOil": 2020,
                "tempFactory": 2023, "pierreRepair": 2023, "kaoyai": 2022,
                "boonNak": 2024,
            }
            year = year_defaults.get(proj_id, 2023)

        projects.append({
            "id": proj_id,
            "name": card.get("name", proj_id),
            "description": card.get("description", ""),
            "images": validated_images,
            "category": category,
            "year": year,
            "featured": proj_id in FEATURED_IDS,
            "client": card.get("client", ""),
            "role": card.get("role", ""),
        })

    # --- Team ---
    print("Extracting team members ...")
    team = extract_team(html)
    print(f"  Found {len(team)} team members")

    # --- Company ---
    company = extract_company(html)

    # --- Assemble output ---
    output = {
        "projects": projects,
        "team": team,
        "company": company,
    }

    # --- Write output ---
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {OUTPUT_FILE}")

    # --- Verification summary ---
    print("\n=== Verification ===")
    print(f"Total projects : {len(projects)}")
    print(f"Total team     : {len(team)}")
    for p in projects:
        status = "OK" if p["images"] else "NO IMAGES"
        print(f"  [{status}] {p['id']:16s} name={p['name']!r:45s} images={len(p['images'])}")

    missing_projects = [p["id"] for p in projects if not p["name"] or p["name"] == p["id"]]
    if missing_projects:
        print(f"\nWARNING: Projects with missing names: {missing_projects}")

    if len(projects) < 12:
        print(f"\nWARNING: Expected 12 projects, got {len(projects)}")
    else:
        print("\nAll 12 projects present.")

    print("\nDone.")


if __name__ == "__main__":
    main()
