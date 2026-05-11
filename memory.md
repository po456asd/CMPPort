# CMPPort Project Memory

Context preservation guide for development continuity when Claude context fills. Explains architecture decisions, procedures, and reference data to avoid code duplication and inconsistent patterns.

---

## Section 1: Architecture Decisions

### Why Factory Pattern for Galleries

**Decision:** Use `createGalleryHandlers(name, config)` factory to generate `{open, next, prev}` handlers dynamically per gallery.

**Why:** Old code had 36 nearly-identical functions (atlasGalleryOpen, atlasGalleryNext, atlasGalleryPrev, quarterGalleryOpen, etc.). Factory eliminates duplication, centralizes logic, scales to new galleries without new functions. Each gallery gets identical behavior from same handler logic.

**Pattern:**
```javascript
const handlers = createGalleryHandlers('atlas', GALLERIES['atlas']);
// Returns: { open: fn, next: fn, prev: fn }
// Same handlers work for every gallery
```

### Why 3 Core Modules, Not 1 File

**Decision:** Split into `modal-core.js`, `thumbnails-core.js`, `gallery-core.js` instead of one monolithic gallery.js.

**Why:** 
- **modal-core** handles ALL modal state + rendering (one source of truth for modal visibility, current gallery, current image index)
- **thumbnails-core** handles thumbnail rendering only (strips, images, click handlers)
- **gallery-core** wires events + manages gallery logic (next/prev/open)

Each module has one responsibility. Easy to test. Easy to find code. Easy to modify without breaking other concerns.

**Responsibility boundaries:**
- Modal: `open(galleryName)`, `close()`, `handleKeyboard()`, `render()`
- Thumbnails: `renderGalleryThumbnails(name)` — creates DOM elements, binds clicks
- Gallery: `createGalleryHandlers()`, `wireGalleryEvents()`, `initAllGalleries()`

### Why Config-Driven Design

**Decision:** GALLERIES object is source of truth. No hardcoded gallery names in functions.

**Why:** Adding a new gallery requires:
- Update GALLERIES config
- Update HTML buttons
- Call `initAllGalleries()` once

Does NOT require writing new functions. Does NOT require copy-pasting code.

**Pattern:**
```javascript
const GALLERIES = {
  atlas: { images: [...], thumbClass: 'gallery-thumb-60' },
  quarter: { images: [...], thumbClass: 'gallery-thumb-60' },
  // Add new gallery here, done
};
```

`initAllGalleries(GALLERIES, galleryState)` loops config, wires all galleries.

### Why Data Attributes for Selectors

**Decision:** HTML buttons use `data-gallery` and `data-action` attributes. JavaScript selects via `[data-gallery="atlas"][data-action="next"]`.

**Why:** Decouples HTML from function names. If function name changes, HTML doesn't break. Easier to find all "atlas" buttons. Cleaner event wiring (no inline onclick attributes).

**Pattern:**
```html
<!-- Old (brittle) -->
<button onclick="atlasGalleryNext()">Next</button>

<!-- New (flexible) -->
<button data-gallery="atlas" data-action="next">Next</button>
```

JavaScript finds and binds:
```javascript
document.querySelectorAll(`[data-gallery="atlas"][data-action="next"]`)
  .forEach(btn => btn.addEventListener('click', handlers.next));
```

---

## Section 2: Procedures

### Add New Gallery (Step-by-Step)

**Step 1: Add to GALLERIES config (index.html `<script>` block)**

```javascript
const GALLERIES = {
  atlas: { images: ['img/atlas/1.jpg', 'img/atlas/2.jpg'], thumbClass: 'gallery-thumb-60' },
  // ... existing galleries ...
  
  // ADD NEW GALLERY HERE
  myNewGallery: {
    images: [
      'img/myNewGallery/1.jpg',
      'img/myNewGallery/2.jpg',
      'img/myNewGallery/3.jpg'
    ],
    thumbClass: 'gallery-thumb-60'
  }
};
```

**Step 2: Initialize galleryState for new gallery**

```javascript
const galleryState = {
  atlas: 0,
  quarter: 0,
  // ... existing galleries ...
  myNewGallery: 0  // ADD THIS
};
```

**Step 3: Add HTML buttons in the gallery section**

```html
<div id="myNewGallery-section">
  <h2>My New Gallery</h2>
  <button data-gallery="myNewGallery" data-action="prev">Previous</button>
  <button data-gallery="myNewGallery" data-action="next">Next</button>
  <div id="myNewGallery-thumbnails" class="thumbnail-strip"></div>
</div>
```

**Step 4: Call `initAllGalleries()` (already done at bottom of `<script>`)**

Done. New gallery works. No new functions needed.

### Add New Project to projects.json

**Structure:** (reference file at `data/projects.json`)

```json
{
  "id": "projectSlug",
  "name": "Project Name",
  "category": "Category (e.g., 'Office Design')",
  "description": "Short description",
  "client": "Client Name",
  "role": "Your Role",
  "year": 2026,
  "images": [
    "img/galleries/projectSlug/image1.jpg",
    "img/galleries/projectSlug/image2.jpg"
  ]
}
```

Add entry to projects.json, images folder automatically syncs with new gallery.

### Modify Modal Behavior

**Example: Change modal close button trigger**

Current: Escape key closes modal (handled in `Modal.handleKeyboard()`).

To add close button in modal:

1. Add button to HTML:
```html
<div id="gallery-modal">
  <button id="modal-close-btn">×</button>
  <!-- ... modal content ... -->
</div>
```

2. Wire in `modal-core.js`, inside `Modal.open()`:
```javascript
open: (galleryName) => {
  Modal.state.visible = true;
  Modal.state.currentGallery = galleryName;
  Modal.state.currentIndex = galleryState[galleryName];
  Modal.render();
  document.addEventListener('keydown', Modal.handleKeyboard);
  
  // ADD THIS
  document.getElementById('modal-close-btn')
    .addEventListener('click', Modal.close);
}
```

3. Clean up in `Modal.close()`:
```javascript
close: () => {
  Modal.state.visible = false;
  Modal.state.currentGallery = null;
  Modal.state.currentIndex = 0;
  document.removeEventListener('keydown', Modal.handleKeyboard);
  // ADD THIS
  const closeBtn = document.getElementById('modal-close-btn');
  if (closeBtn) closeBtn.removeEventListener('click', Modal.close);
  document.getElementById('gallery-modal').style.display = 'none';
}
```

### Fix Gallery Issues

**Issue: Images not loading**
- Check `images` array in GALLERIES config for typos
- Verify image files exist in `img/galleries/[galleryName]/`
- Check browser console for 404 errors

**Issue: Next/Previous buttons don't work**
- Verify HTML buttons have correct `data-gallery` and `data-action` attributes
- Check that gallery name matches a key in GALLERIES config
- Verify `initAllGalleries()` was called

**Issue: Modal doesn't close on Escape**
- Check that `Modal.handleKeyboard()` is bound in `Modal.open()`
- Verify `Modal.close()` removes the event listener to avoid duplicates

**Issue: Thumbnails don't render**
- Check `renderGalleryThumbnails(name)` is called in `wireGalleryEvents()`
- Verify `<div id="[galleryName]-thumbnails">` exists in HTML
- Check browser console for errors in thumbnail click handler

---

## Section 3: Reference

### Current Galleries (12 total)

| Gallery ID | Display Name | Image Count |
|-----------|--------------|------------|
| atlas | Atlas | ~6 images |
| quarter | Quarter | ~4 images |
| obk | OBK | ~5 images |
| trp | TRP | ~4 images |
| kbh | KBH | ~3 images |
| pryd | Pryd | ~4 images |
| obkf | OBKF | ~3 images |
| thaiOil | Thai Oil | ~4 images |
| tempFactory | Temp Factory | ~4 images |
| pierreRepair | Pierre Repair | ~3 images |
| kaoyai | Kaoyai | ~4 images |
| boonNak | Boon Nak | ~4 images |

### projects.json Schema

```json
{
  "company": {
    "name": "CMP Management Asia",
    "tagline": "Company tagline"
  },
  "projects": [
    {
      "id": "unique-slug",
      "name": "Display Name",
      "category": "Project Category",
      "description": "One-line description",
      "client": "Client Name (optional)",
      "role": "Your Role (optional)",
      "year": 2026,
      "images": [
        "img/galleries/slug/image1.jpg",
        "img/galleries/slug/image2.jpg"
      ]
    }
  ]
}
```

### File Structure

```
CMPPort/
├── index.html                 (Main gallery page, config + scripts)
├── js/
│   ├── modal-core.js         (Modal state + rendering)
│   ├── thumbnails-core.js    (Thumbnail rendering)
│   └── gallery-core.js       (Factory, event wiring, initialization)
├── css/
│   └── style.css             (Styling for galleries, modal, thumbnails)
├── img/
│   └── galleries/
│       ├── atlas/
│       ├── quarter/
│       └── ... (one folder per gallery)
├── data/
│   └── projects.json         (Project metadata)
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-11-website-gallery-refactor-design.md
```

### Global Objects

**galleryState** (in index.html `<script>`)
```javascript
const galleryState = {
  atlas: 0,      // Current image index for atlas gallery
  quarter: 0,
  // ... one per gallery
};
```
Used to track which image is visible in each gallery. Updated by `next()`, `prev()`, thumbnail clicks.

**GALLERIES** (in index.html `<script>`)
```javascript
const GALLERIES = {
  atlas: {
    images: ['img/galleries/atlas/1.jpg', ...],
    thumbClass: 'gallery-thumb-60'
  },
  // ... one per gallery
};
```
Source of truth. Config-driven. No hardcoded names in functions.

**Modal** (in modal-core.js)
```javascript
const Modal = {
  state: { visible, currentGallery, currentIndex },
  open(galleryName) { ... },
  close() { ... },
  render() { ... },
  handleKeyboard(e) { ... }
};
```
Centralized modal logic. Single state object. All modal behavior flows through this.

---

## Section 4: Common Mistakes

### ❌ Mistake 1: Copy-Pasting Old Hardcoded Functions

**Wrong:**
```javascript
// DO NOT DO THIS
function myNewGalleryOpen() {
  galleryState.myNewGallery = 0;
  Modal.open('myNewGallery');
}

function myNewGalleryNext() {
  const len = GALLERIES.myNewGallery.images.length;
  galleryState.myNewGallery = (galleryState.myNewGallery + 1) % len;
  updateGallery('myNewGallery');
}
```

**Why wrong:** Duplicates factory logic. If you fix a bug in `next()`, this copy won't get the fix.

**Right:** Just add to GALLERIES config. `createGalleryHandlers()` generates identical handlers.

### ❌ Mistake 2: Modifying HTML onclick Directly

**Wrong:**
```html
<button onclick="customGalleryNext()">Next</button>
```

**Why wrong:** Couples HTML to function names. If function name changes, HTML breaks silently.

**Right:**
```html
<button data-gallery="myNewGallery" data-action="next">Next</button>
```

`wireGalleryEvents()` finds and binds automatically.

### ❌ Mistake 3: Forgetting `initAllGalleries()` Call

**Wrong:**
```html
<script>
  const GALLERIES = { ... };
  const galleryState = { ... };
  // Forgot to call initAllGalleries()!
</script>
```

**Result:** Buttons don't work. Event listeners not wired.

**Right:**
```html
<script>
  const GALLERIES = { ... };
  const galleryState = { ... };
  initAllGalleries(GALLERIES, galleryState);  // ← Must call
</script>
```

### ❌ Mistake 4: Hardcoding Gallery Names in New Functions

**Wrong:**
```javascript
function updateAtlasCounter() {
  document.getElementById('atlas-counter').textContent = galleryState.atlas;
}
```

**Why wrong:** Doesn't scale. Each gallery needs a copy.

**Right:** Use config-driven approach. Pass gallery name as parameter:
```javascript
function updateCounter(galleryName) {
  document.getElementById(galleryName + '-counter').textContent = 
    galleryState[galleryName];
}
```

Then call from `updateGallery(name)` which already knows the gallery name.

### ❌ Mistake 5: Modifying Modal State Outside Modal Object

**Wrong:**
```javascript
// Somewhere in gallery-core.js
Modal.state.visible = true;  // DO NOT DO THIS
Modal.state.currentIndex = 5;
```

**Why wrong:** State becomes scattered. Hard to debug. Modal.render() may not know state changed.

**Right:** Call Modal methods:
```javascript
Modal.open('atlasGallery');
// Modal.open() sets state internally and calls render()
```

---

## Refactor Summary

**Before:** 2000+ lines, 36 duplicate functions, 72+ event listeners scattered
**After:** 220 lines, 3 core modules, 1 factory + config-driven initialization

**Key improvements:**
- Factory pattern eliminates function duplication
- Config-driven design (GALLERIES) scales to new galleries without code changes
- Modal object centralizes state + rendering
- Data attributes decouple HTML from function names
- Three focused modules (modal, thumbnails, gallery) vs one monolithic file

