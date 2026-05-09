# Plan: PPTX Presentation Generation from CMPPort Site Data

## Requirements Summary

Generate automated PowerPoint presentations from CMPPort website data using three presentation types:
1. **Project Portfolio/Showcase** — All projects with images and descriptions
2. **Team & Company Profile** — Team bios, company info, selected projects  
3. **Annual/Status Reports** — Timeline/summary view of multiple projects

**Data Access**: Hybrid approach combining HTML parsing (index.html) + structured data file (JSON/CSV)
**Workflow**: Interactive — Claude asks user what to include before generation

---

## Acceptance Criteria

- [ ] Parse index.html to extract project names, images, team bios, descriptions
- [ ] Create structured data file (JSON) with all project metadata, team info, image paths
- [ ] Implement interactive workflow that prompts user for:
  - Presentation type (Portfolio / Team Profile / Annual Report)
  - Scope (which projects, which team members, date range)
  - Customization (title, subtitle, color scheme if applicable)
- [ ] Generate PPTX with python-pptx library containing:
  - Title slide with project/company name
  - Project slides with images and descriptions
  - Team member slides with bios
  - Summary/closing slides
  - Proper formatting and layout
- [ ] Save generated PPTX to output directory
- [ ] Support regeneration with different parameters without manual reparse

---

## Implementation Steps

### Phase 1: Data Extraction & Structure (Files: `extract-site-data.py`, `data/projects.json`, `data/team.json`)

**Step 1.1**: Parse `index.html` to extract:
- All 12 project galleries (names, image URLs, descriptions)
- Team member names and biographies
- Hero images and gallery images per project
- Company/branding info (colors, fonts used)

**Step 1.2**: Create `data/projects.json` structure:
```json
{
  "projects": [
    {
      "id": "atlas",
      "name": "Atlas",
      "description": "...",
      "images": ["img/proj/atlas/1.jpg", ...],
      "category": "construction|real_estate|...",
      "year": 2024,
      "featured": true
    }
  ],
  "team": [
    {
      "name": "...",
      "bio": "...",
      "role": "..."
    }
  ],
  "company": {
    "name": "CMPPort",
    "tagline": "...",
    "colors": {...}
  }
}
```

**Step 1.3**: Save JSON to `data/projects.json` for reuse (no re-parsing needed)

---

### Phase 2: Interactive Presentation Builder (`generate-pptx.py`)

**Step 2.1**: Create interactive CLI that prompts user:
```
1. Select presentation type: [1] Portfolio [2] Team Profile [3] Annual Report
2. Select projects to include: [checkboxes or number list]
3. Include team members? Yes/No. If yes, which ones?
4. Presentation title: [input]
5. Subtitle/client name: [input]
```

**Step 2.2**: Based on selection, dynamically build presentation structure:

- **Portfolio/Showcase**: 
  - Title slide
  - 1 slide per project (image + description)
  - Closing slide

- **Team Profile**:
  - Title slide
  - Company overview slide
  - 1 slide per team member (photo placeholder + bio)
  - Featured projects carousel (4-6 key projects)
  - Closing slide

- **Annual/Status Report**:
  - Title slide (year/date range)
  - Summary statistics slide (# projects completed, team size)
  - Timeline: 1 slide per project (year-grouped)
  - Team snapshot
  - Closing/next steps

**Step 2.3**: Validate selections (ensure images exist, team members valid, etc.)

---

### Phase 3: PPTX Generation (`pptx-generator.py`)

**Step 3.1**: Use `python-pptx` library to build deck:
- Set up slide master with consistent formatting
- Add text boxes, images, shapes with proper alignment
- Handle image sizing/aspect ratio
- Apply colors from `projects.json` color config

**Step 3.2**: For each slide type, implement:
- **Title Slide**: Company name, project/report title, date
- **Project Slide**: Project image (full width), name, description (2-3 lines), key stats
- **Team Slide**: Team member name, bio text, placeholder for profile photo (if available)
- **Summary Slide**: Statistics, next steps, contact info

**Step 3.3**: Save PPTX to `output/<presentation-name>_<timestamp>.pptx`

---

### Phase 4: Integration & Testing

**Step 4.1**: Create main entry point (`main.py`):
- Check if `data/projects.json` exists; if not, run data extraction
- Launch interactive CLI
- Pass selection to PPTX generator
- Return file path to output PPTX

**Step 4.2**: Test each presentation type:
- Portfolio with all projects
- Team Profile with subset of team
- Annual Report with date filters

**Step 4.3**: Verify:
- Images load correctly in generated PPTX
- Text formatting is readable
- File saves without errors
- Can regenerate different presentations without reparse

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Image paths incorrect in HTML** | Parse relative paths, resolve to absolute; validate image files exist before adding to PPTX |
| **Large image files slow PPTX generation** | Compress images before embedding; test with full gallery (12 projects) |
| **HTML structure changes break parser** | Document current HTML structure; use CSS selectors for robustness; fallback to manual data file |
| **User selects no projects/team** | Validate selections; enforce minimum (e.g., at least 1 project for Portfolio) |
| **PPTX file too large** | Monitor file size; apply compression; limit image quality if needed |

---

## Verification Steps

1. **Data Extraction**: 
   - Run parser, verify `data/projects.json` contains all 12 projects with correct image count
   - Compare parsed data against `index.html` manually (spot check 3 projects)

2. **Interactive Workflow**:
   - Generate Portfolio with all projects → verify slide count = projects + 2 (title + closing)
   - Generate Team Profile → verify all selected team members appear
   - Generate Annual Report → verify projects grouped by year

3. **PPTX Output**:
   - Open generated PPTX in PowerPoint/LibreOffice
   - Verify images display correctly
   - Check text is readable and not cut off
   - Verify slide transitions and layout consistency

4. **Edge Cases**:
   - Generate report with single project
   - Generate with no team members (Portfolio only)
   - Re-run generation 2x without re-parsing (verify data reuse)

---

## File Structure

```
CMPPort/
├── data/
│   ├── projects.json          (extracted site data)
│   └── team.json              (if separated)
├── scripts/
│   ├── extract-site-data.py   (HTML parser)
│   ├── generate-pptx.py       (PPTX builder)
│   ├── pptx-generator.py      (PPTX engine)
│   └── main.py                (entry point)
├── output/                    (generated PPTXs)
└── templates/
    └── config.json            (optional: branding, colors)
```

---

## Success Criteria

- ✅ User runs `python main.py` → interactive CLI appears
- ✅ User selects presentation type and projects
- ✅ PPTX generated in < 30s
- ✅ Output file opens in PowerPoint with correct formatting
- ✅ All selected projects and team members appear
- ✅ Images display without errors
- ✅ Can regenerate different presentations from same data without re-parsing

